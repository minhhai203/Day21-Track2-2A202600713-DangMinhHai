# Screenshots nộp bài — MLOps Lab Day 21

Thư mục này chứa bằng chứng nộp bài theo thứ tự yêu cầu trong README lab.

| # | File | Nội dung | Rubric |
|---|------|----------|--------|
| 01 | `01-github-actions-overview.png` | Tổng quan 2 lần chạy pipeline | CI/CD |
| 02 | `02-github-actions-run1-eval-gate-failed.png` | Run #1: Eval fail, Deploy skip (acc < 0.70) | Eval gate |
| 03 | `03-github-actions-run2-all-jobs-green.png` | Run #2: 4 jobs xanh (Bước 3) | CI/CD + Bước 3 |
| 04 | `04-s3-bucket-dvc-and-models.png` | S3 bucket: folders `dvc/` + `models/` | DVC |
| 05 | `05-s3-dvc-data-files.png` | DVC data trong `dvc/files/md5/` | DVC |
| 06 | `06-s3-model-latest-pkl.png` | Model `models/latest/model.pkl` (61.6 MB) | Serving |
| 07 | `07-curl-api-health-predict.png` | Kết quả curl `/health` + `/predict` | Serving |
| 07 | `07-curl-api-output.txt` | Raw output curl (backup) | Serving |
| 08 | `08-mlflow-experiments-top-runs.png` | Top 8 MLflow experiments |
| 09 | `09-bonus-performance-report.txt` | Bonus 3: confusion matrix + classification report |

**Repo:** https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai
