---
description: Agen proyek Warkop USB MicroScope (aplikasi desktop PySide6/OpenCV) — aturan arsitektur, gerbang kualitas, dan konvensi.
mode: primary
---

# Warkop Performance USB MicroScope — Panduan Agen

Panduan agen proyek untuk bekerja di repositori ini dengan Kilo.

## Tentang Proyek

Aplikasi desktop lintas-platform untuk USB digital microscope, dibangun dengan
Python 3.10+, PySide6 (Qt), dan OpenCV. Nama paket `warkop-performance-usb-microscope`;
namespace import `microscope`; nama tampilan **Warkop Performance USB MicroScope**.

## Gerbang Kualitas (WAJIB)

Setiap milestone WAJIB lolos **semua tiga** sebelum dinyatakan selesai:

```bash
pytest
ruff check .
mypy src tests
```

Jangan pernah menyatakan selesai sebelum menjalankan dan meloloskan semuanya.

## Arsitektur (hormati atau dokumentasikan penyimpangan)

```
main.py → app/application.py
    └── MainWindow (ui/main_window.py)
            ├── CameraView (ui/camera_view.py)   frame + zoom + overlay + processing
            └── ControlsPanel (ui/controls_panel.py)
                    └── CameraWorker (ui/camera_worker.py, di QThread)
                            ├── CameraManager (camera/camera_manager.py)
                            │       └── camera_backend.py (HANYA OpenCV di sini)
                            └── VideoRecorder (recording/recorder.py)
```

Logika bisnis **tidak bergantung pada UI**:
- `camera/` — deteksi, siklus hidup, kapabilitas, kontrol.
- `imaging/` — pemrosesan non-destruktif (`FrameProcessor`).
- `measurement/` — `Calibration`, `Point`, alat ukur garis/sudut/lingkaran/persegi (murni).
- `storage/` — `CalibrationStore`, `ProjectStore`, `ImageStore` (JSON).

## Aturan Keras

1. **Jangan pernah lakukan I/O kamera di thread UI.** Hubungkan panggilan
   mutasi pada worker via `@Slot()` + `invokeMethod` (BlockingQueued) — lihat
   `CameraWorker.stop_from_main_thread`.
2. **Jangan pernah hard-code indeks kamera 0.** Selalu enumerasi.
3. **Jangan asumsikan semua kamera mendukung semua properti** — gunakan
   `CameraCapabilities`.
4. **Frame mentah jangan pernah dimutasi.** Pemrosesan bekerja pada salinan
   (`FrameProcessor`).
5. **Tidak ada state mutable global.** Gunakan frozen dataclass; injeksi via
   konstruktor.

## Kekeliruan macOS / PySide6 (ingat selalu)

- Melukis `QPainter` hidup pada `QPixmap` yang datanya dari buffer numpy yang
  segera dibebaskan → segfault saat teardown. Selalu `QImage.copy()` sebelum
  tampil.
- Menghentikan `QTimer` dari thread non-pemilik memicu warning
  `QObject::killTimer`. Hentikan di thread pemiliknya
  (`CameraWorker.stop`, dipanggil via `stop_from_main_thread`).

## Pengujian

- `tests/unit/` — cepat, OpenCV di-mock, tanpa Qt bila mungkin, tanpa hardware.
- `tests/integration/` — `pytest-qt`, boleh buat instance widget.
- Logika non-trivial butuh minimal satu pengujian yang dijalankan; one-liner
  tidak butuh.
- Perilaku hardware didokumentasikan sebagai tes manual, bukan dipalsukan
  sebagai tes otomatis.

## Konvensi

- Anotasi tipe pada semua method publik (mypy strict).
- Frozen dataclass untuk config/value object.
- snake_case untuk fungsi/variabel, PascalCase untuk kelas. Panjang baris 100.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`,
  `chore:`, `perf:`.
- Perbarui README/docs saat perilaku atau alur publik berubah.
