#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROJECTSZAI — FASE 1: DIAGNOSTICO DE MEMORIA, RUNTIME E INTEGRIDAD
================================================================
Un solo archivo, Python 3.8+ y biblioteca estandar. Pensado para Windows 10/11.

MODO PREDETERMINADO: SOLO LECTURA.
- No modifica config.txt ni archivos del proyecto.
- No inicia, detiene ni reinicia llama-server.
- No cambia flags ni carga el modelo.
- Solo ejecuta llama-server --version/--help, consulta endpoints GET locales,
  lee metadatos GGUF y captura telemetria del sistema.
- La prueba activa de aislamiento de caché solo se ejecuta con --probe-cache
  y confirmacion interactiva exacta. No la ejecutes mientras alguien chatea.

Salida: carpeta salidas/FASE1_<fecha>/ con JSON, Markdown, muestras y ZIP.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION_SCRIPT = "1.0.0"
REPO_NAME = "liontestv-stack/projectsZai"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9931
MAX_CAPTURE_CHARS = 2_000_000


def now_stamp() -> str:
    return dt.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")


def json_dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def text_dump(path: Path, value: str) -> None:
    path.write_text(value[:MAX_CAPTURE_CHARS], encoding="utf-8", errors="replace")


def parse_config(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def find_paths() -> Dict[str, Optional[Path]]:
    script = Path(__file__).resolve()
    script_dir = script.parent
    roots: List[Path] = []
    try:
        roots.append(script.parents[3])
    except IndexError:
        pass
    roots.extend([script_dir, Path.cwd()])
    unique_roots: List[Path] = []
    for root in roots:
        if root not in unique_roots:
            unique_roots.append(root)

    config_candidates: List[Path] = []
    flags_candidates: List[Path] = []
    for root in unique_roots:
        config_candidates.extend([
            root / "InformacionCritica" / "configs" / "config.txt",
            root / "config.txt",
            root / "configs" / "config.txt",
        ])
        flags_candidates.extend([
            root / "InformacionCritica" / "configs" / "llama-flags-nuevo.txt",
            root / "llama-flags-nuevo.txt",
            root / "configs" / "llama-flags-nuevo.txt",
        ])
    config_candidates.append(Path(r"D:\ZLia\config.txt"))
    flags_candidates.extend([
        Path(r"D:\ZLia\llama-flags-nuevo.txt"),
        Path(r"D:\ZLia\InformacionCritica\configs\llama-flags-nuevo.txt"),
    ])

    def first_existing(candidates: Iterable[Path]) -> Optional[Path]:
        seen = set()
        for candidate in candidates:
            try:
                key = str(candidate.resolve()).lower()
            except Exception:
                key = str(candidate).lower()
            if key in seen:
                continue
            seen.add(key)
            if candidate.is_file():
                return candidate.resolve()
        return None

    return {
        "script": script,
        "script_dir": script_dir,
        "repo_root_guess": unique_roots[0] if unique_roots else Path.cwd(),
        "config": first_existing(config_candidates),
        "flags_dump": first_existing(flags_candidates),
    }


def split_flags(value: str) -> List[str]:
    if not value.strip():
        return []
    try:
        return shlex.split(value, posix=False)
    except ValueError:
        return value.split()


def flag_tokens(tokens: Iterable[str]) -> List[str]:
    found = []
    for token in tokens:
        clean = token.strip().strip('"').strip("'")
        if re.fullmatch(r"--[A-Za-z][A-Za-z0-9-]*", clean) or re.fullmatch(r"-[A-Za-z][A-Za-z0-9-]*", clean):
            found.append(clean)
    return found


def flags_from_text(text: str) -> set:
    found = set()
    for match in re.finditer(r"(?<![A-Za-z0-9_])(--[A-Za-z][A-Za-z0-9-]*|-[A-Za-z][A-Za-z0-9-]*)(?=\s|,|$)", text):
        found.add(match.group(1))
    return found


def run_capture(command: List[str], timeout: int = 20) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, check=False, shell=False)
        return {
            "ok": True,
            "returncode": proc.returncode,
            "duration_s": round(time.perf_counter() - started, 3),
            "stdout": proc.stdout[:MAX_CAPTURE_CHARS],
            "stderr": proc.stderr[:MAX_CAPTURE_CHARS],
            "command": command,
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        return {"ok": False, "error": "timeout", "timeout_s": timeout,
                "stdout": out, "stderr": err, "command": command}
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "command": command}


def sha256_file(path: Path, max_bytes: int = 300 * 1024 * 1024) -> Optional[str]:
    try:
        if path.stat().st_size > max_bytes:
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except Exception:
        return None


def parse_gguf_header(path: Path) -> Dict[str, Any]:
    """Lee solo cabecera y metadatos GGUF; no recorre ni carga tensores."""
    wanted_suffixes = (
        "general.architecture", "general.name", "general.file_type",
        "general.quantization_version", ".block_count", ".expert_count",
        ".expert_used_count", ".expert_shared_count", ".leading_dense_block_count",
        ".attention.head_count", ".attention.head_count_kv",
        ".expert_feed_forward_length",
    )
    type_sizes = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}

    def read_exact(handle, count: int) -> bytes:
        data = handle.read(count)
        if len(data) != count:
            raise EOFError("GGUF truncado mientras se leian metadatos")
        return data

    def read_string(handle) -> str:
        size = struct.unpack("<Q", read_exact(handle, 8))[0]
        if size > 64 * 1024 * 1024:
            raise ValueError("cadena GGUF de tamano anomalo")
        return read_exact(handle, size).decode("utf-8", "replace")

    def read_value(handle, kind: int, keep: bool) -> Any:
        if kind == 8:
            value = read_string(handle)
            return value if keep else None
        if kind == 9:
            elem_type, count = struct.unpack("<IQ", read_exact(handle, 12))
            if count > 100_000_000:
                raise ValueError("array GGUF de tamano anomalo")
            if elem_type == 8:
                values = []
                for _ in range(count):
                    item = read_string(handle)
                    if keep and len(values) < 1000:
                        values.append(item)
                return values if keep else None
            size = type_sizes.get(elem_type)
            if size is None:
                raise ValueError("tipo de array GGUF desconocido: %s" % elem_type)
            byte_count = count * size
            if byte_count > 2 * 1024 * 1024 * 1024:
                raise ValueError("array GGUF demasiado grande para saltar")
            if keep and count <= 1000:
                raw = read_exact(handle, byte_count)
                if elem_type == 0:
                    return list(raw)
                return {"array_count": count, "element_type": elem_type, "raw_bytes": len(raw)}
            handle.seek(byte_count, os.SEEK_CUR)
            return {"array_count": count, "element_type": elem_type} if keep else None
        if kind == 7:
            value = struct.unpack("<B", read_exact(handle, 1))[0] != 0
            return value if keep else None
        formats = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 10: "<Q", 11: "<q", 12: "<d"}
        fmt = formats.get(kind)
        if not fmt:
            raise ValueError("tipo de metadato GGUF desconocido: %s" % kind)
        value = struct.unpack(fmt, read_exact(handle, struct.calcsize(fmt)))[0]
        return value if keep else None

    result: Dict[str, Any] = {"path": str(path), "ok": False}
    try:
        with path.open("rb") as handle:
            if read_exact(handle, 4) != b"GGUF":
                raise ValueError("el archivo no empieza con GGUF")
            version, tensor_count, metadata_count = struct.unpack("<IQQ", read_exact(handle, 20))
            metadata: Dict[str, Any] = {}
            for _ in range(metadata_count):
                key = read_string(handle)
                kind = struct.unpack("<I", read_exact(handle, 4))[0]
                keep = any(key == suffix or key.endswith(suffix) for suffix in wanted_suffixes)
                value = read_value(handle, kind, keep)
                if keep:
                    metadata[key] = value
            result.update({"ok": True, "version": version, "tensor_count": tensor_count,
                           "metadata_count": metadata_count, "metadata": metadata,
                           "bytes_read_position": handle.tell()})
    except Exception as exc:
        result["error"] = repr(exc)
    return result


def windows_memory_snapshot() -> Dict[str, Any]:
    if os.name != "nt":
        return {"available": False, "reason": "requiere Windows"}

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    state = MEMORYSTATUSEX()
    state.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        return {"available": False, "error": "GlobalMemoryStatusEx fallo"}
    gib = 1024 ** 3
    return {
        "available": True,
        "memory_load_percent": int(state.dwMemoryLoad),
        "physical_total_gib": round(state.ullTotalPhys / gib, 3),
        "physical_available_gib": round(state.ullAvailPhys / gib, 3),
        "pagefile_commit_limit_gib": round(state.ullTotalPageFile / gib, 3),
        "pagefile_available_gib": round(state.ullAvailPageFile / gib, 3),
        "virtual_total_gib": round(state.ullTotalVirtual / gib, 3),
        "virtual_available_gib": round(state.ullAvailVirtual / gib, 3),
    }


def powershell_json(script: str, timeout: int = 40) -> Dict[str, Any]:
    exe = shutil.which("powershell.exe") or shutil.which("powershell")
    if not exe:
        return {"ok": False, "error": "PowerShell no encontrado"}
    result = run_capture([exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], timeout)
    if not result.get("ok"):
        return result
    raw = result.get("stdout", "").strip()
    try:
        result["data"] = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        result["parse_error"] = "PowerShell no devolvio JSON valido"
    return result


def redact_command_line(value: str) -> str:
    if not value:
        return value
    value = re.sub(r'(?i)(--api-key(?:-file)?|--hf-token)(?:\s+|=)("[^"]*"|\S+)', r"\1 [REDACTED]", value)
    value = re.sub(r"(?i)(HF_TOKEN=)\S+", r"\1[REDACTED]", value)
    return value


def get_process_snapshot() -> Dict[str, Any]:
    if os.name != "nt":
        return {"ok": False, "reason": "consulta detallada implementada para Windows"}
    ps = r'''
$ErrorActionPreference = 'Stop'
$items = @(Get-CimInstance Win32_Process -Filter "Name='llama-server.exe'" | ForEach-Object {
  [pscustomobject]@{ ProcessId=$_.ProcessId; ParentProcessId=$_.ParentProcessId;
    Name=$_.Name; ExecutablePath=$_.ExecutablePath; CommandLine=$_.CommandLine;
    WorkingSetBytes=$_.WorkingSetSize; PageFaults=$_.PageFaults;
    KernelModeTime=$_.KernelModeTime; UserModeTime=$_.UserModeTime }
})
ConvertTo-Json -InputObject $items -Depth 4 -Compress
'''
    result = powershell_json(ps, timeout=30)
    data = result.get("data") if result.get("ok") else None
    if isinstance(data, dict):
        data = [data]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("CommandLine"):
                item["CommandLine"] = redact_command_line(str(item["CommandLine"]))
    result["data"] = data
    # stdout contiene la misma serializacion CIM; eliminarlo para no conservar
    # una segunda copia de la linea de comandos sin redactar.
    result.pop("stdout", None)
    result.pop("stderr", None)
    return result


def get_os_snapshot() -> Dict[str, Any]:
    if os.name != "nt":
        return {"platform": platform.platform(), "note": "muestra completa requiere Windows"}
    ps = r'''
$ErrorActionPreference = 'Stop'
$o = Get-CimInstance Win32_OperatingSystem
$c = Get-CimInstance Win32_Processor | Select-Object -First 1
$r = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
 [pscustomobject]@{CapacityBytes=$_.Capacity; SpeedMHz=$_.Speed; Manufacturer=$_.Manufacturer; PartNumber=$_.PartNumber}
})
[pscustomobject]@{Caption=$o.Caption; Version=$o.Version; BuildNumber=$o.BuildNumber;
 OSArchitecture=$o.OSArchitecture; Processor=$c.Name; Cores=$c.NumberOfCores;
 LogicalProcessors=$c.NumberOfLogicalProcessors; MaxClockMHz=$c.MaxClockSpeed;
 MemoryModules=$r} | ConvertTo-Json -Depth 5 -Compress
'''
    return powershell_json(ps, timeout=30)


def get_memory_counters(sample_seconds: int, interval: int) -> Dict[str, Any]:
    if os.name != "nt":
        return {"ok": False, "reason": "contadores Windows no disponibles"}
    samples = max(2, min(60, int(sample_seconds / max(1, interval))))
    ps = r'''
$ErrorActionPreference = 'Stop'
try {
 $paths = @('\Memory\Page Reads/sec', '\Memory\Pages Input/sec')
 $sets = Get-Counter -Counter $paths -SampleInterval INTERVAL -MaxSamples SAMPLES
 $rows = @()
 foreach ($set in $sets) { foreach ($s in $set.CounterSamples) {
   $rows += [pscustomobject]@{Timestamp=$set.Timestamp.ToString('o'); Path=$s.Path; CookedValue=[math]::Round($s.CookedValue,3)}
 }}
 [pscustomobject]@{ok=$true; samples=$rows} | ConvertTo-Json -Depth 5 -Compress
} catch {
 [pscustomobject]@{ok=$false; error=$_.Exception.Message; note='Puede ser necesario usar nombres de contadores localizados'} | ConvertTo-Json -Compress
}
'''.replace("INTERVAL", str(interval)).replace("SAMPLES", str(samples))
    return powershell_json(ps, timeout=sample_seconds + 30)


def parse_nvidia_csv(line: str) -> List[str]:
    return [part.strip() for part in next(csv.reader([line]))]


def get_gpu_snapshot() -> Dict[str, Any]:
    nvsmi = shutil.which("nvidia-smi")
    if not nvsmi:
        return {"available": False, "reason": "nvidia-smi no encontrado en PATH"}
    query = "name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,clocks.gr,clocks.mem,power.draw"
    result = run_capture([nvsmi, "--query-gpu=" + query, "--format=csv,noheader,nounits"], timeout=15)
    if not result.get("ok") or result.get("returncode") != 0:
        return {"available": False, "error": result.get("stderr") or result.get("stdout") or result.get("error")}
    columns = [x.strip() for x in query.split(",")]
    rows = []
    for line in result.get("stdout", "").splitlines():
        if line.strip():
            rows.append(dict(zip(columns, parse_nvidia_csv(line))))
    return {"available": True, "rows": rows, "stderr": result.get("stderr", "")}


def sample_gpu(duration: int, interval: int) -> List[Dict[str, Any]]:
    nvsmi = shutil.which("nvidia-smi")
    if not nvsmi or duration <= 0:
        return []
    query = "name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,clocks.gr,power.draw"
    end = time.monotonic() + duration
    samples = []
    while True:
        result = run_capture([nvsmi, "--query-gpu=" + query, "--format=csv,noheader,nounits"], timeout=10)
        timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        if result.get("ok") and result.get("returncode") == 0:
            keys = query.split(",")
            for line in result.get("stdout", "").splitlines():
                if line.strip():
                    row = dict(zip(keys, parse_nvidia_csv(line)))
                    row["timestamp"] = timestamp
                    samples.append(row)
        if time.monotonic() >= end:
            break
        time.sleep(max(1, interval))
    return samples


def http_get(url: str, timeout: int = 3) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "projectsZai-phase1-diagnostic/" + VERSION_SCRIPT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raw = raw[:2 * 1024 * 1024]
            text = raw.decode("utf-8", "replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return {"ok": True, "status": response.status, "data": data}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def sanitize_slots(data: Any) -> Any:
    """No guardar prompts ni contenido textual de slots: solo estado y contadores."""
    allowed = {"id", "slot_id", "is_processing", "n_ctx", "n_past", "n_predict",
               "n_tokens", "n_tokens_cached", "n_cached", "state", "prompt_tokens",
               "task_id", "speculative"}
    if isinstance(data, list):
        return [{k: v for k, v in item.items() if k in allowed}
                for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in allowed:
                result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = sanitize_slots(value)
        return result
    return {"type": type(data).__name__}


def server_endpoints(host: str, port: int) -> Dict[str, Any]:
    base = "http://%s:%d" % (host, port)
    result = {"base_url": base}
    for endpoint in ("/health", "/slots", "/metrics"):
        data = http_get(base + endpoint)
        if endpoint == "/slots" and data.get("ok"):
            data["data"] = sanitize_slots(data.get("data"))
        if endpoint == "/metrics" and data.get("ok") and isinstance(data.get("data"), str):
            data["data"] = data["data"][:100000]
        result[endpoint] = data
    return result


def cache_canary_request(base: str, marker: str, timeout: int = 120) -> Dict[str, Any]:
    body = {
        "model": "apex35b",
        "messages": [
            {"role": "system", "content": "Devuelve solamente el identificador que aparece en el mensaje del usuario. No agregues explicaciones."},
            {"role": "user", "content": "Identificador requerido: " + marker + ". Copialo exactamente."},
        ],
        "temperature": 0.1,
        "top_p": 1.0,
        "max_tokens": 32,
        "stream": False,
    }
    raw = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base + "/v1/chat/completions", data=raw,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "projectsZai-phase1-cache-probe/" + VERSION_SCRIPT})
    try:
        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        elapsed = time.perf_counter() - started
        choices = payload.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        content = str(message.get("content") or "")
        reasoning = str(message.get("reasoning_content") or "")
        return {"ok": True, "marker": marker, "elapsed_s": round(elapsed, 3),
                "content": content[:2000], "reasoning_content": reasoning[:2000],
                "usage": payload.get("usage"), "model": payload.get("model")}
    except Exception as exc:
        return {"ok": False, "marker": marker, "error": repr(exc)}


def run_cache_probe(host: str, port: int, rounds: int) -> Dict[str, Any]:
    print("\nATENCION: prueba ACTIVA de caché. Enviara solicitudes al modelo y ocupara slots.")
    print("Cierra CHATEAR-QWEN y confirma que nadie esta usando el servidor.")
    expected = "PROBAR_CACHE_EN_SERVIDOR_QUIETO"
    try:
        confirmation = input("Escribe exactamente %s para continuar: " % expected).strip()
    except EOFError:
        return {"executed": False, "reason": "sin consola interactiva para confirmar"}
    if confirmation != expected:
        return {"executed": False, "reason": "confirmacion no valida"}
    base = "http://%s:%d" % (host, port)
    health = http_get(base + "/health")
    if not health.get("ok"):
        return {"executed": False, "reason": "servidor no saludable", "health": health}
    results = []
    contamination = []
    for round_index in range(1, rounds + 1):
        nonce = hashlib.sha256((str(time.time_ns()) + str(round_index)).encode()).hexdigest()[:10].upper()
        a = "PZA_A_%s_%d" % (nonce, round_index)
        b = "PZA_B_%s_%d" % (nonce, round_index)
        pair: Dict[str, Any] = {"round": round_index, "markers": [a, b]}
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(cache_canary_request, base, marker): marker for marker in (a, b)}
            responses = {}
            for future in as_completed(futures):
                marker = futures[future]
                try:
                    responses[marker] = future.result()
                except Exception as exc:
                    responses[marker] = {"ok": False, "error": repr(exc)}
        pair["responses"] = responses
        for own, other in ((a, b), (b, a)):
            response = responses.get(own, {})
            text_value = response.get("content", "") + " " + response.get("reasoning_content", "")
            if response.get("ok") and other in text_value:
                contamination.append({"round": round_index, "response_marker": own,
                                      "foreign_marker": other, "finding": "foreign marker detected"})
            if response.get("ok") and own not in text_value:
                pair.setdefault("copy_misses", []).append(own)
        results.append(pair)
    status = "POTENTIAL_CONTAMINATION" if contamination else "NO_CONTAMINATION_OBSERVED"
    return {"executed": True, "status": status, "rounds": rounds,
            "contamination_findings": contamination, "results": results,
            "limitations": [
                "Prueba heuristica: no demuestra ausencia total de contaminacion.",
                "Un fallo de copia del modelo es inconcluso; solo un marcador ajeno es senal positiva.",
                "La prueba crea estado de caché y puede alterar rendimiento temporalmente.",
                "No equivale a una auditoria formal de aislamiento de slots.",
            ]}


def build_report(summary: Dict[str, Any]) -> str:
    cfg = summary.get("config", {})
    flags = summary.get("flag_audit", {})
    memory = summary.get("memory", {})
    gpu = summary.get("gpu", {})
    endpoints = summary.get("server", {})
    lines = [
        "# Informe Fase 1 — projectsZai", "",
        "- Fecha local: %s" % summary.get("timestamp_local"),
        "- Script: %s" % summary.get("script_version"),
        "- Modo: %s" % ("prueba activa de caché incluida" if summary.get("cache_probe", {}).get("executed") else "solo lectura"),
        "", "## Resumen ejecutivo", "",
        "- Config encontrada: %s" % cfg.get("path", "no"),
        "- Ejecutable llama-server: %s" % summary.get("runtime", {}).get("server_exe", "no configurado"),
        "- Modelo: %s" % summary.get("model", {}).get("path", "no configurado"),
        "- Proceso llama-server detectado: %s" % len((summary.get("processes", {}).get("data") or [])),
        "- API local saludable: %s" % endpoints.get("/health", {}).get("ok", False),
        "- Revision manual de aislamiento de caché requerida: %s" % summary.get("cache_config_review", {}).get("needs_manual_isolation_review", "n/d"),
        "- RAM disponible: %s GiB" % memory.get("physical_available_gib", "n/d"),
        "- Carga RAM: %s%%" % memory.get("memory_load_percent", "n/d"),
        "- GPU: %s" % (gpu.get("rows", [{}])[0].get("name", "no detectada") if gpu.get("rows") else "no detectada"),
        "", "## Auditoria de flags", "",
        "- Flags configuradas: %d" % len(flags.get("configured", [])),
        "- Presentes en ayuda del ejecutable: %d" % len(flags.get("supported_by_runtime", [])),
        "- No vistas en ayuda del ejecutable: %s" % (", ".join(flags.get("not_seen_in_runtime", [])) or "ninguna"),
        "- No vistas en el dump permitido: %s" % (", ".join(flags.get("not_seen_in_dump", [])) or "ninguna"),
        "", "## Interpretacion de memoria", "",
        "Los contadores Page Reads/sec y Pages Input/sec son del sistema completo, no exclusivos de llama-server. Deben interpretarse junto con RAM disponible, memoria comprometida, proceso y actividad de disco.",
        "", "## Integridad de caché", "",
    ]
    cache_review = summary.get("cache_config_review", {})
    lines.append("- Politica observada en config: %s" % json.dumps(cache_review, ensure_ascii=False))
    probe = summary.get("cache_probe", {})
    if probe.get("executed"):
        lines.append("- Resultado heuristico: **%s**" % probe.get("status"))
        lines.append("- Marcadores ajenos detectados: %d" % len(probe.get("contamination_findings", [])))
        lines.append("- Este resultado no demuestra ausencia de fallos si no se observa contaminacion.")
    else:
        lines.append("- Prueba activa no ejecutada. La inspeccion por defecto no envia prompts.")
        lines.append("- Motivo: %s" % probe.get("reason", "no solicitada"))
    lines.extend([
        "", "## Limitaciones", "",
        "- Esta captura no cambia flags ni compara rendimiento entre configuraciones.",
        "- Un muestreo corto no demuestra que no exista paginacion bajo carga.",
        "- La ayuda del ejecutable confirma opciones reconocidas, no que una optimizacion mejore el rendimiento.",
        "- La lectura de cabecera GGUF no valida todos los tensores ni la integridad completa del archivo.",
        "- La prueba de canarios es heuristica y solo debe ejecutarse con el servidor libre.",
        "", "## Archivos incluidos", "",
        "Revisa phase1_report.json y las capturas en bruto incluidas en este paquete.", "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostico de solo lectura para Fase 1 de projectsZai")
    parser.add_argument("--host", default=DEFAULT_HOST, help="host local de llama-server")
    parser.add_argument("--port", type=int, default=None, help="puerto; por defecto se lee de config.txt")
    parser.add_argument("--sample-seconds", type=int, default=12, help="duracion de muestreo de GPU/contadores (0 desactiva)")
    parser.add_argument("--sample-interval", type=int, default=2, help="intervalo de muestreo en segundos")
    parser.add_argument("--probe-cache", action="store_true", help="ejecuta prueba activa de canarios; requiere confirmacion exacta")
    parser.add_argument("--probe-rounds", type=int, default=3, help="rondas de prueba activa (1-5)")
    parser.add_argument("--output", default=None, help="carpeta de salida personalizada")
    args = parser.parse_args()

    print("=" * 72)
    print("PROJECTSZAI — FASE 1 / DIAGNOSTICO")
    print("Modo predeterminado: SOLO LECTURA; no se cambia la configuracion.")
    print("=" * 72)

    paths = find_paths()
    config_path = paths.get("config")
    flags_path = paths.get("flags_dump")
    config: Dict[str, str] = {}
    config_error = None
    if config_path:
        try:
            config = parse_config(config_path)
        except Exception as exc:
            config_error = repr(exc)

    port = args.port or (int(config.get("PUERTO", DEFAULT_PORT)) if config.get("PUERTO", "").isdigit() else DEFAULT_PORT)
    server_exe = Path(config.get("RUTA_SERVER", "")) if config.get("RUTA_SERVER") else None
    model_path = Path(config.get("RUTA_MODELO", "")) if config.get("RUTA_MODELO") else None

    output_root = Path(args.output).expanduser().resolve() if args.output else (paths["script_dir"] / "salidas")
    run_dir = output_root / ("FASE1_" + now_stamp())
    run_dir.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "script_version": VERSION_SCRIPT, "repo": REPO_NAME,
        "timestamp_local": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host_info": {"platform": platform.platform(), "python": sys.version,
                      "machine": platform.machine(), "processor_env": platform.processor(),
                      "cwd": str(Path.cwd())},
        "paths": {k: str(v) if v else None for k, v in paths.items()},
        "config": {"path": str(config_path) if config_path else None, "error": config_error,
                   "keys": sorted(config.keys()), "values": {k: v for k, v in config.items() if not re.search(r"token|api.?key|secret|password", k, re.I)}},
        "runtime": {}, "model": {}, "flag_audit": {}, "memory": {}, "gpu": {},
        "processes": {}, "server": {}, "cache_probe": {"executed": False, "reason": "no solicitada"},
    }

    print("[1/8] Sistema, memoria y GPU...")
    summary["os_details"] = get_os_snapshot()
    summary["memory"] = windows_memory_snapshot()
    summary["gpu"] = get_gpu_snapshot()

    print("[2/8] Ejecutable y version de llama.cpp...")
    summary["runtime"]["server_exe"] = str(server_exe) if server_exe else None
    runtime_help_text = ""
    if server_exe and server_exe.is_file():
        summary["runtime"]["exe_size_bytes"] = server_exe.stat().st_size
        summary["runtime"]["exe_sha256"] = sha256_file(server_exe)
        version_result = run_capture([str(server_exe), "--version"], timeout=20)
        help_result = run_capture([str(server_exe), "--help"], timeout=30)
        summary["runtime"]["version"] = {k: v for k, v in version_result.items() if k not in ("stdout", "stderr")}
        summary["runtime"]["version_text"] = (version_result.get("stdout", "") + "\n" + version_result.get("stderr", "")).strip()
        summary["runtime"]["help"] = {k: v for k, v in help_result.items() if k not in ("stdout", "stderr")}
        runtime_help_text = help_result.get("stdout", "") + "\n" + help_result.get("stderr", "")
        text_dump(run_dir / "runtime_version.txt", summary["runtime"]["version_text"])
        text_dump(run_dir / "runtime_help.txt", runtime_help_text)
        summary["runtime"]["help_excerpt"] = runtime_help_text[:12000]
    else:
        summary["runtime"]["error"] = "RUTA_SERVER no existe o no se encontro config.txt"

    print("[3/8] Auditoria de flags permitidas vs build instalado...")
    configured_tokens: List[str] = []
    configured_by_key: Dict[str, List[str]] = {}
    for key in ("FLAGS_BASE", "SAMPLING", "FLAGS_GANADORAS"):
        tokens = split_flags(config.get(key, ""))
        configured_by_key[key] = flag_tokens(tokens)
        configured_tokens.extend(configured_by_key[key])
    configured_unique = sorted(set(configured_tokens))
    dump_text = ""
    if flags_path:
        try:
            dump_text = flags_path.read_text(encoding="utf-8-sig", errors="replace")
        except Exception as exc:
            summary["flag_audit"]["dump_error"] = repr(exc)
    dump_flags = flags_from_text(dump_text)
    runtime_flags = flags_from_text(runtime_help_text)
    summary["flag_audit"].update({
        "dump_path": str(flags_path) if flags_path else None,
        "configured_by_key": configured_by_key,
        "configured": configured_unique,
        "dump_flag_count": len(dump_flags),
        "runtime_help_flag_count": len(runtime_flags),
        "not_seen_in_dump": sorted(set(configured_unique) - dump_flags) if dump_flags else configured_unique,
        "supported_by_runtime": sorted(set(configured_unique) & runtime_flags) if runtime_flags else [],
        "not_seen_in_runtime": sorted(set(configured_unique) - runtime_flags) if runtime_flags else configured_unique,
        "note": "La comparacion de ayuda es una deteccion textual; revisar falsos negativos si la build agrupa alias o cambia formato.",
    })
    summary["flag_audit"]["cmoe_and_ncmoe_both_configured"] = ("-cmoe" in configured_unique and "-ncmoe" in configured_unique)
    base_tokens = split_flags(config.get("FLAGS_BASE", ""))
    summary["flag_audit"]["np2"] = ("-np" in base_tokens and base_tokens.index("-np") + 1 < len(base_tokens) and base_tokens[base_tokens.index("-np") + 1] == "2")
    summary["flag_audit"]["kv_types"] = {
        "K": config.get("FLAGS_BASE", "").split("-ctk", 1)[-1].split()[0] if "-ctk" in config.get("FLAGS_BASE", "") else None,
        "V": config.get("FLAGS_BASE", "").split("-ctv", 1)[-1].split()[0] if "-ctv" in config.get("FLAGS_BASE", "") else None,
    }
    all_config_tokens = split_flags(" ".join(config.get(k, "") for k in ("FLAGS_BASE", "SAMPLING", "FLAGS_GANADORAS")))
    def read_option_value(option_names):
        for option in option_names:
            if option in all_config_tokens:
                idx = all_config_tokens.index(option)
                if idx + 1 < len(all_config_tokens):
                    return all_config_tokens[idx + 1]
        return None
    cache_idle_state = ("disabled" if "--no-cache-idle-slots" in all_config_tokens
                        else "enabled" if "--cache-idle-slots" in all_config_tokens
                        else "default_enabled")
    kv_unified_state = ("enabled" if ("-kvu" in all_config_tokens or "--kv-unified" in all_config_tokens)
                        else "disabled" if ("-no-kvu" in all_config_tokens or "--no-kv-unified" in all_config_tokens)
                        else "default_conditional_on_auto_parallel")
    np_value = read_option_value(["-np", "--parallel"])
    summary["cache_config_review"] = {
        "parallel_slots_configured": np_value,
        "cache_prompt": "disabled" if "--no-cache-prompt" in all_config_tokens else "enabled_or_default",
        "cache_ram_mib": read_option_value(["-cram", "--cache-ram"]) or "default_8192_mib",
        "cache_idle_slots": cache_idle_state,
        "kv_unified": kv_unified_state,
        "needs_manual_isolation_review": bool(np_value and np_value.isdigit() and int(np_value) > 1
                                             and cache_idle_state != "disabled"
                                             and kv_unified_state == "default_conditional_on_auto_parallel"),
        "note": "Revision de configuracion, no diagnostico de vulnerabilidad. Confirmar comportamiento con la build instalada y el test controlado.",
    }
    if flags_path:
        text_dump(run_dir / "allowed_flags_dump.txt", dump_text)

    print("[4/8] GGUF: solo cabecera y metadatos...")
    summary["model"]["path"] = str(model_path) if model_path else None
    if model_path and model_path.is_file():
        stat = model_path.stat()
        summary["model"].update({"exists": True, "size_bytes": stat.st_size,
                                 "size_gib": round(stat.st_size / (1024 ** 3), 3),
                                 "modified_local": dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
                                 "gguf_header": parse_gguf_header(model_path)})
    else:
        summary["model"].update({"exists": False, "error": "modelo no encontrado en RUTA_MODELO"})

    print("[5/8] Proceso llama-server y endpoints locales GET...")
    summary["processes"] = get_process_snapshot()
    running_processes = (summary["processes"].get("data") or []) if isinstance(summary["processes"], dict) else []
    runtime_active_flags = set()
    for process in running_processes:
        command_line = process.get("CommandLine", "") if isinstance(process, dict) else ""
        try:
            runtime_active_flags.update(flag_tokens(shlex.split(command_line, posix=False)))
        except Exception:
            runtime_active_flags.update(flag_tokens(command_line.split()))
    summary["runtime"]["active_process_count"] = len(running_processes)
    summary["runtime"]["active_process_flags"] = sorted(runtime_active_flags)
    summary["runtime"]["configured_flags_missing_from_active_process"] = (
        sorted(set(configured_unique) - runtime_active_flags) if running_processes else []
    )
    summary["runtime"]["active_flags_not_in_config"] = (
        sorted(runtime_active_flags - set(configured_unique)) if running_processes else []
    )
    summary["server"] = server_endpoints(args.host, port)

    print("[6/8] Contadores de paginacion y muestreo GPU...")
    sample_seconds = max(0, min(60, args.sample_seconds))
    sample_interval = max(1, min(10, args.sample_interval))
    if sample_seconds > 0:
        # Tomar contadores de memoria y telemetria GPU en paralelo para que
        # ambas series temporales describan aproximadamente la misma carga.
        with ThreadPoolExecutor(max_workers=2) as executor:
            memory_future = executor.submit(get_memory_counters, sample_seconds, sample_interval)
            gpu_future = executor.submit(sample_gpu, sample_seconds, sample_interval)
            summary["memory_counters"] = memory_future.result()
            summary["gpu_samples"] = gpu_future.result()
    else:
        summary["memory_counters"] = {"ok": False, "reason": "muestreo desactivado"}
        summary["gpu_samples"] = []
    summary["memory_after_sample"] = windows_memory_snapshot()
    summary["processes_after_sample"] = get_process_snapshot()

    print("[7/8] Prueba de integridad de caché...")
    if args.probe_cache:
        summary["cache_probe"] = run_cache_probe(args.host, port, max(1, min(5, args.probe_rounds)))
    else:
        summary["cache_probe"] = {"executed": False, "reason": "no solicitada; modo seguro por defecto"}

    print("[8/8] Guardando informe y paquete...")
    json_dump(run_dir / "phase1_report.json", summary)
    text_dump(run_dir / "phase1_report.md", build_report(summary))
    json_dump(run_dir / "processes.json", summary.get("processes"))
    json_dump(run_dir / "processes_after_sample.json", summary.get("processes_after_sample"))
    json_dump(run_dir / "server_endpoints.json", summary.get("server"))
    json_dump(run_dir / "memory_counters.json", summary.get("memory_counters"))
    json_dump(run_dir / "cache_probe.json", summary.get("cache_probe"))
    if summary.get("gpu_samples"):
        with (run_dir / "gpu_samples.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary["gpu_samples"][0].keys()))
            writer.writeheader()
            writer.writerows(summary["gpu_samples"])
    else:
        text_dump(run_dir / "gpu_samples.csv", "timestamp,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,clocks.gr,power.draw\n")

    archive = run_dir.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for item in run_dir.rglob("*"):
            if item.is_file():
                zipf.write(item, arcname=str(item.relative_to(run_dir)))

    print("\nTERMINADO")
    print("Informe:  %s" % (run_dir / "phase1_report.md"))
    print("JSON:     %s" % (run_dir / "phase1_report.json"))
    print("Paquete:  %s" % archive)
    print("\nNo se cambiaron flags ni config.txt.")
    if summary.get("cache_probe", {}).get("status") == "POTENTIAL_CONTAMINATION":
        print("ALERTA: aparecieron marcadores de otra peticion. Conserva el ZIP y no uses esta prueba como demostracion definitiva.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario. Los archivos ya guardados permanecen en salidas/.")
        raise SystemExit(130)
