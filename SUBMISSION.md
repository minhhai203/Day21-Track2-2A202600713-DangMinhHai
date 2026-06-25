# Nộp bài — MLOps CI/CD Lab (Day 21)

**Sinh viên:** Đặng Minh Hải  
**Repo:** https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai  
**Cloud:** AWS (S3 + EC2, region `us-east-1`)

---

## 1. URL repo GitHub public

https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai

---

## 2. Chuỗi screenshot (theo thứ tự lab)

Tất cả file nằm trong thư mục [`screenshots/`](screenshots/).

| Thứ tự | File | Mô tả |
|--------|------|-------|
| 1 | [`08-mlflow-experiments-top-runs.png`](screenshots/08-mlflow-experiments-top-runs.png) | MLflow: ≥3 thí nghiệm với params khác nhau, log accuracy + f1_score |
| 2a | [`02-github-actions-run1-eval-gate-failed.png`](screenshots/02-github-actions-run1-eval-gate-failed.png) | GitHub Actions Run #1 — Eval fail (accuracy 0.686 < 0.70), Deploy bị chặn |
| 2b | [`03-github-actions-run2-all-jobs-green.png`](screenshots/03-github-actions-run2-all-jobs-green.png) | GitHub Actions Run #2 — 4 jobs xanh (Bước 3) |
| 2c | [`01-github-actions-overview.png`](screenshots/01-github-actions-overview.png) | Tổng quan cả 2 lần chạy pipeline |
| 3 | [`07-curl-api-health-predict.png`](screenshots/07-curl-api-health-predict.png) | `curl /health` → `{"status":"ok"}` và `/predict` → kết quả hợp lệ |
| 4a | [`04-s3-bucket-dvc-and-models.png`](screenshots/04-s3-bucket-dvc-and-models.png) | S3 bucket `mlops-lab-949678235460-hai` |
| 4b | [`05-s3-dvc-data-files.png`](screenshots/05-s3-dvc-data-files.png) | DVC data đã push lên S3 |
| 4c | [`06-s3-model-latest-pkl.png`](screenshots/06-s3-model-latest-pkl.png) | Model artifact trên S3 |

**Pipeline runs:**
- Run #1: https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai/actions/runs/28147842679
- Run #2: https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai/actions/runs/28147947918

---

## 3. Báo cáo ngắn (1 trang A4)

### Bộ siêu tham số đã chọn

```yaml
n_estimators: 300
max_depth: null
min_samples_split: 2
```

**Lý do:** Sau nhiều thí nghiệm trên MLflow, bộ params này cho accuracy cao nhất. Trên tập 2998 mẫu đạt **0.686** (dưới ngưỡng deploy 0.70). Sau Bước 3 (5996 mẫu), cùng bộ params đạt **~0.754**, vượt ngưỡng và pipeline deploy thành công.

### Khó khăn và cách giải quyết

1. **Accuracy 2998 mẫu < 0.70:** Eval gate chặn Deploy ở Run #1 — đúng thiết kế lab. Giải quyết bằng Bước 3: gộp thêm 2998 mẫu từ `train_phase2.csv` → accuracy 0.754.

2. **Repo fork — GitHub Actions bị disable:** GitHub tắt workflow mặc định trên fork. Bật thủ công qua tab Actions ("I understand my workflows, go ahead and enable them").

3. **IAM thiếu quyền S3:** User `ai-lab-user` ban đầu không tạo được bucket. Thêm `AmazonS3FullAccess` vào group `AI-Lab-Group`.

4. **Chuyển GCP → AWS:** Cập nhật `requirements.txt` (`dvc[s3]`, `boto3`), `src/serve.py`, `.github/workflows/mlops.yml` cho S3/EC2.

### Kết quả metrics

| Giai đoạn | Train samples | Accuracy | F1 |
|-----------|---------------|----------|-----|
| Bước 2 (Run #1) | 2998 | ~0.686 | ~0.685 |
| Bước 3 (Run #2) | 5996 | ~0.754 | ~0.753 |

### API endpoint

- **Health:** `GET http://13.218.84.151:8000/health` → `{"status":"ok"}`
- **Predict:** `POST http://13.218.84.151:8000/predict` → `{"prediction":0,"label":"thap"}`

---

## Checklist rubric (80 điểm chính)

| Tiêu chí | Điểm | Bằng chứng |
|----------|------|------------|
| MLflow ≥3 runs, params khác nhau | 12 | `08-mlflow-experiments-top-runs.png` |
| Log accuracy + f1_score | 8 | MLflow screenshot + code `train.py` |
| Phân tích best params | 4 | Báo cáo trên + `params.yaml` |
| DVC + cloud storage | 12 | `04`, `05` S3 screenshots |
| CI/CD Test/Train/Deploy xanh | 16 | `03` Run #2 |
| Eval gate chặn deploy | 4 | `02` Run #1 |
| VM `/predict` đúng | 12 | `07` curl screenshot |
| Bước 3 tự động hóa | 12 | `03` + commit message data |
| **Tổng** | **80** | |

**Bonus:** Đã triển khai code 5/5. Bonus 1 cần thêm DagsHub secrets + screenshot. Điểm dự kiến: **96–100/100**.

## Bonus — Bằng chứng bổ sung

| Bonus | File / Link |
|-------|-------------|
| 2 Multi-algorithm | MLflow runs + bảng trong `MY_LAB_NOTES.md` |
| 3 Performance report | [`screenshots/09-bonus-performance-report.txt`](screenshots/09-bonus-performance-report.txt) |
| 4 Rollback | Log job Deploy: `Rollback check: new=..., previous=...` |
| 5 Data drift | `label_distribution` + `drift_warning` trong `outputs/metrics.json` |
| 1 DagsHub | ⚠️ Thêm `MLFLOW_TRACKING_URI` + `MLFLOW_TRACKING_TOKEN` secrets, chụp DagsHub UI |
