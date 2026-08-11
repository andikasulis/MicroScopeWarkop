# AGENTS.md — Warkop Performance USB MicroScope

Dokumen instruksi untuk agen AI yang bekerja di repositori ini.

## Ringkasan

Aplikasi desktop untuk USB digital microscope: Python 3.10+, PySide6 (Qt),
OpenCV. Nama tampilan **Warkop Performance USB MicroScope**, namespace
import `microscope`, nama paket `warkop-performance-usb-microscope`.

## Gerbang Kualitas (wajib sebelum selesai)

```bash
pytest
ruff check .
mypy src tests
```

## Tahapan (jangan lompat)

1. Baca dokumentasi proyek (`README.md`, `docs/DEVELOPMENT.md`).
2. Inspeksi arsitektur saat ini (lihat `src/microscope/`).
3. Identifikasi implementasi yang sudah ada.
4. Buat rencana implementasi singkat.
5. Terapkan perubahan terkecil yang benar.
6. Tambah/perbarui tes.
7. Jalankan `pytest`, `ruff check .`, `mypy src tests`.
8. Perbaiki kegagalan sampai lolos.
9. Perbarui dokumentasi bila arsitektur/alur berubah.
10. Ringkas perubahan.

## Arsitektur Utama

- `ui/CameraWorker` hidup di `QThread`; **jangan** lakukan I/O kamera di thread UI.
- Backend OpenCV hanya di `camera/camera_backend.py`.
- Logika bisnis (`measurement/`, `imaging/`, `storage/`) bersih dari Qt.
- Jangan hard-code indeks kamera 0; selalu enumerasi (`CameraManager`).
- Pemrosesan frame wajib non-destruktif (salinan).
- Tidak ada state mutable global; gunakan frozen dataclass.

## Kesalahan Umum macOS/PySide6

- `QPainter` pada `QPixmap` ber-buffer numpy yang akan dibebaskan → segfault.
  Selalu `QImage.copy()`.
- Stop `QTimer` dari thread lain → warning `QObject::killTimer`. Gunakan
  `stop` via thread pemilik (`CameraWorker.stop_from_main_thread`).

## Konvensi

- Anotasi tipe pada semua method publik.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `perf:`.
- Panjang baris 100.
