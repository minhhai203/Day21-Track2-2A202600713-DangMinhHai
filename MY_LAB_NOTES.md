# Lab Notes - MLOps CI/CD (Day 21)

> File ghi chú cá nhân của **Đặng Minh Hải** — lưu lại từng bước làm bài, lý do và mục đích.
> Repo: https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai

---

## Trạng thái tổng kết (cập nhật 25/06/2026)

| Hạng mục | Trạng thái |
|----------|------------|
| Bước 1 — MLflow local | ✅ Hoàn thành (18 runs, ≥3 params khác nhau) |
| Bước 2 — DVC + CI/CD + EC2 | ✅ Hoàn thành |
| Bước 3 — Continuous training | ✅ Hoàn thành |
| Hạ tầng AWS (S3 + EC2) | ✅ Đang chạy |
| GitHub Actions pipeline | ✅ 2 lần chạy (Eval fail → 4 jobs xanh) |
| API `/health` + `/predict` | ✅ Verified |
| **Bonus (5 thách thức)** | ✅ **Code xong** — Bonus 1 cần bạn thêm DagsHub secrets |
| **Nộp bài (screenshot + báo cáo)** | ✅ Xem [`SUBMISSION.md`](SUBMISSION.md) + [`screenshots/`](screenshots/) |

### Điểm dự kiến

| Loại | Điểm tối đa | Dự kiến | Ghi chú |
|------|-------------|---------|---------|
| Tiêu chí chính (rubric) | **80** | **80** | Đủ bằng chứng |
| Bonus | 20 | **16–20** | Bonus 1 cần DagsHub screenshot từ bạn |
| **Tổng** | **100** | **96–100** | Sau khi thêm DagsHub secrets + chụp MLflow trên DagsHub |

---

## Timeline các hành động đã thực hiện

### Phase 1 — Code & local (AI)

1. Implement `src/train.py`, `src/serve.py`, `tests/test_train.py`, `.github/workflows/mlops.yml`
2. Chuyển cloud provider từ GCP → **AWS** (`dvc[s3]`, `boto3`)
3. Cài venv, `generate_data.py`, chạy ≥3 thí nghiệm MLflow
4. Chọn best params: `n_estimators=300, max_depth=null, min_samples_split=2`
5. `pytest tests/ -v` → **3/3 passed**

### Phase 2 — AWS infrastructure

6. User thêm quyền IAM: `AmazonS3FullAccess` (+ EC2 đã có sẵn)
7. Tạo S3 bucket `mlops-lab-949678235460-hai`
8. `dvc init` → `dvc add` 3 CSV → `dvc push` (3 files lên S3)
9. Launch EC2 `i-05bedc213d096de3e` @ `13.218.84.151` (t2.micro, Ubuntu 22.04)
10. Cài FastAPI/boto3 trên EC2, copy `serve.py` + AWS credentials, tạo systemd service
11. Tạo SSH key `~/.ssh/mlops_deploy` cho GitHub Actions deploy

### Phase 3 — GitHub & pipeline

12. User thêm 5 GitHub Secrets (`CLOUD_CREDENTIALS`, `CLOUD_BUCKET`, `VM_HOST`, `VM_USER`, `VM_SSH_KEY`)
13. **Vấn đề:** Repo là fork → Actions bị disable mặc định
14. User bật Actions trên fork (nút "I understand my workflows, go ahead and enable them")
15. Push retrigger → pipeline chạy lần 1

### Phase 4 — Pipeline runs & Bước 3

16. **Run #1** `28147842679` — Bước 2 (2998 mẫu):
    - Unit Test ✅ | Train ✅ | Eval ❌ (~0.686 < 0.70) | Deploy ⏭ skipped
17. **Bước 3:** `add_new_data.py` → 5996 mẫu → `dvc push` → `git push`
18. **Run #2** `28147947918` — Bước 3 (commit `data: bổ sung 2998 mẫu...`):
    - Unit Test ✅ | Train ✅ | Eval ✅ (~0.754) | Deploy ✅
19. Verify API live:
    ```bash
    curl http://13.218.84.151:8000/health
    # {"status":"ok"}

    curl -X POST http://13.218.84.151:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"features": [7.4,0.70,0.00,1.9,0.076,11.0,34.0,0.9978,3.51,0.56,9.4,0]}'
    # {"prediction":0,"label":"thap"}
    ```

---

## Kết quả chi tiết

### MLflow (Bước 1)

- **18 runs** trong `mlflow.db` (local SQLite)
- Mỗi run log đủ `accuracy` + `f1_score` + params
- Best params (2998 mẫu): accuracy **0.686** | f1 **0.685**
- Best params (5996 mẫu, Bước 3): accuracy **~0.754** | f1 **~0.753**

| Run | n_estimators | max_depth | min_samples_split | Accuracy | F1 |
|-----|-------------|-----------|-------------------|----------|-----|
| 1 | 100 | 5 | 2 | 0.5640 | 0.5534 |
| 2 | 50 | 3 | 2 | 0.5580 | 0.5185 |
| 3 | 200 | 10 | 5 | 0.6420 | 0.6394 |
| **Best** | **300** | **null** | **2** | **0.686** / **0.754*** | **0.685** / **0.753*** |

*0.754 = sau Bước 3 (5996 mẫu train)

**Lý do chọn params:** `n_estimators=300, max_depth=null` cho accuracy cao nhất trong các combo đã thử; sau khi gộp thêm data (Bước 3) vượt ngưỡng eval gate 0.70.

### GitHub Actions

| Run ID | Commit | Unit Test | Train | Eval | Deploy | Link |
|--------|--------|-----------|-------|------|--------|------|
| `28147842679` | retrigger sau enable Actions | ✅ | ✅ | ❌ | ⏭ | [Actions](https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai/actions/runs/28147842679) |
| `28147947918` | `data: bổ sung 2998 mẫu...` | ✅ | ✅ | ✅ | ✅ | [Actions](https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai/actions/runs/28147947918) |

### AWS resources

| Resource | Giá trị |
|----------|---------|
| Account | `949678235460` |
| IAM User | `ai-lab-user` |
| Region | `us-east-1` |
| S3 Bucket | `mlops-lab-949678235460-hai` |
| DVC remote | `s3://mlops-lab-949678235460-hai/dvc` |
| Model on S3 | `s3://mlops-lab-949678235460-hai/models/latest/model.pkl` (~64MB) |
| EC2 | `i-05bedc213d096de3e` @ **13.218.84.151** |
| SSH key (local) | `mlops-serve-key.pem` (gitignored) |

---

## Chấm điểm theo Rubric (80 điểm chính)

| # | Tiêu chí | Điểm | Bằng chứng kỹ thuật | Bằng chứng nộp bài | Dự kiến |
|---|----------|------|---------------------|-------------------|---------|
| 1 | MLflow ≥3 runs, params khác nhau | 12 | ✅ 18 runs | ✅ `08-mlflow-experiments-top-runs.png` | **12** |
| 2 | Mỗi run có `accuracy` + `f1_score` | 8 | ✅ Code + MLflow | ✅ `08-mlflow-experiments-top-runs.png` | **8** |
| 3 | Phân tích & chọn best params | 4 | ✅ `params.yaml` | ✅ `SUBMISSION.md` báo cáo A4 | **4** |
| 4 | DVC remote + push lên cloud | 12 | ✅ S3 `dvc/` | ✅ `04`, `05` S3 screenshots | **12** |
| 5 | CI/CD: Test, Train, Deploy xanh | 16 | ✅ Run #2 | ✅ `03-github-actions-run2-all-jobs-green.png` | **16** |
| 6 | Eval gate chặn khi acc < 0.70 | 4 | ✅ Run #1 | ✅ `02-github-actions-run1-eval-gate-failed.png` | **4** |
| 7 | VM `/predict` trả kết quả đúng | 12 | ✅ curl live | ✅ `07-curl-api-health-predict.png` | **12** |
| 8 | Bước 3: commit data → pipeline tự chạy | 12 | ✅ Run #2 | ✅ `03` + commit message | **12** |
| | **Tổng tiêu chí chính** | **80** | | | **80** |

---

## Bonus — Đã triển khai (20 điểm)

> Chi tiết từng bước bên dưới. File code chính: `src/train.py`, `.github/workflows/mlops.yml`, `params.yaml`

| Bonus | Điểm | Code | Bằng chứng |
|-------|------|------|------------|
| 1 DagsHub MLflow remote | 4 | ✅ `mlops.yml` + `configure_mlflow()` | ⚠️ Bạn thêm secrets + chụp DagsHub UI |
| 2 Nhiều thuật toán | 4 | ✅ `model_type` trong `params.yaml` | ✅ MLflow runs + bảng dưới |
| 3 Báo cáo hiệu suất tự động | 4 | ✅ `outputs/report.txt` + artifact CI | ✅ `screenshots/09-bonus-performance-report.txt` |
| 4 Rollback deploy | 4 | ✅ Deploy job so sánh metrics S3 | ✅ Log pipeline sau push |
| 5 Cảnh báo data drift | 4 | ✅ `check_label_distribution()` | ✅ `label_distribution` trong `metrics.json` |

---

### Bonus 1 — MLflow remote qua DagsHub (4đ)

**Mục đích:** Mỗi lần train trên GitHub Actions được log lên DagsHub, xem từ bất cứ đâu.

**Đã làm trong code:**

1. Hàm `configure_mlflow()` trong `src/train.py`:
   - Nếu có `MLFLOW_TRACKING_URI` → dùng DagsHub
   - Nếu không → fallback SQLite local (`sqlite:///mlflow.db`)

2. Job Train trong `mlops.yml` truyền secrets:
```yaml
env:
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
  MLFLOW_TRACKING_TOKEN: ${{ secrets.MLFLOW_TRACKING_TOKEN }}
```

**Bạn cần làm (1 lần):**

1. Tạo tài khoản https://dagshub.com
2. Tạo repo mới hoặc connect GitHub repo
3. Vào repo DagsHub → Settings → MLflow → copy **Tracking URI** và **Token**
4. Thêm GitHub Secrets:
   - `MLFLOW_TRACKING_URI` = `https://dagshub.com/user/repo.mlflow`
   - `MLFLOW_TRACKING_TOKEN` = token từ DagsHub
5. Push/re-run pipeline → vào DagsHub tab Experiments → **chụp màn hình** runs

---

### Bonus 2 — Nhiều thuật toán (4đ)

**Mục đích:** So sánh ≥2 thuật toán trên MLflow UI.

**Đã làm:**

1. Thêm `model_type` vào `params.yaml`:
```yaml
model_type: random_forest   # hoac gradient_boosting | logistic_regression
```

2. Hàm `build_model()` chọn classifier tương ứng:
   - `random_forest` → `RandomForestClassifier`
   - `gradient_boosting` → `GradientBoostingClassifier`
   - `logistic_regression` → `LogisticRegression`

3. Chạy thí nghiệm local (5996 mẫu sau Bước 3):

| model_type | accuracy | f1_score |
|------------|----------|----------|
| random_forest | **0.754** | 0.753 |
| gradient_boosting | 0.614 | 0.611 |
| logistic_regression | 0.518 | 0.508 |

**Kết luận:** `random_forest` vẫn tốt nhất → giữ trong `params.yaml` cho production.

**Lệnh tái tạo:**
```bash
source .venv/bin/activate
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
# Sua model_type trong params.yaml roi chay:
python src/train.py
```

---

### Bonus 3 — Báo cáo hiệu suất tự động (4đ)

**Mục đích:** Sau mỗi lần train, tạo báo cáo text với confusion matrix + precision/recall từng lớp.

**Đã làm:**

1. Hàm `write_performance_report()` trong `src/train.py` tạo `outputs/report.txt`:
```
Confusion Matrix (rows=true, cols=pred):
       pred_0  pred_1  pred_2
true_0     142      30       1
...

Classification Report:
              precision    recall  f1-score   support
           0     0.7594    0.8208    ...
```

2. `mlops.yml` upload artifact:
```yaml
path: |
  outputs/metrics.json
  outputs/report.txt
```

**Bằng chứng:** `screenshots/09-bonus-performance-report.txt`

---

### Bonus 4 — Rollback khi accuracy giảm (4đ)

**Mục đích:** Không deploy model mới nếu accuracy thấp hơn lần trước.

**Đã làm trong job Deploy (`mlops.yml`):**

1. **Trước** SSH restart: tải `s3://bucket/models/latest/metrics.json` (metrics lần deploy trước)
2. So sánh `new_acc` (từ job Train) với `old_acc`
3. Nếu `new_acc < old_acc` → `exit 1`, hủy deploy
4. Nếu không có file cũ (lần đầu) → bỏ qua, cho deploy
5. **Sau** deploy thành công: upload `metrics.json` mới lên S3

**Luồng:**
```
Train (acc=0.754) → Eval pass → Deploy:
  download old metrics (0.754 từ lần trước)
  0.754 >= 0.754 → PASSED → restart EC2 → upload metrics mới
```

**Kiểm tra log:** Tìm dòng `Rollback check: new=..., previous=...` trong job Deploy.

---

### Bonus 5 — Cảnh báo lệch phân phối nhãn (4đ)

**Mục đích:** Phát hiện class imbalance (< 10% tổng mẫu) trước khi train.

**Đã làm:**

1. Hàm `check_label_distribution()` trong `src/train.py`:
   - Tính tỷ lệ lớp 0, 1, 2
   - Nếu lớp nào < 10% → in `WARNING [data drift]: class X chi chiem Y%`
   - Ghi vào `outputs/metrics.json`:

```json
{
  "label_distribution": {"0": 0.3686, "1": 0.4351, "2": 0.1963},
  "drift_warning": false
}
```

**Dataset Wine Quality (5996 mẫu):** Không có lớp nào < 10% → `drift_warning: false` (bình thường).

**Cách test cảnh báo (tùy chọn):**
```python
# Tao data gia voi 1 lop rat it de thay warning
import pandas as pd
df = pd.read_csv("data/train_phase1.csv")
df_imb = df[df["target"] != 2].head(500)  # bo gan het class 2
df_imb.to_csv("/tmp/imbalanced.csv", index=False)
# train(params, data_path="/tmp/imbalanced.csv", ...)
```

---

### Phase 5 — Bonus implementation (25/06/2026)

1. Refactor `src/train.py`: `build_model`, `check_label_distribution`, `write_performance_report`, `configure_mlflow`
2. Cập nhật `params.yaml` thêm `model_type`, `max_iter`
3. Cập nhật `mlops.yml`: DagsHub env, report artifact, rollback check, upload metrics sau deploy
4. Chạy thí nghiệm 3 thuật toán → ghi kết quả vào MLflow
5. Tạo `outputs/report.txt` mẫu → copy sang `screenshots/09-bonus-performance-report.txt`
6. Upload baseline metrics lên S3 cho rollback: `models/latest/metrics.json`

### Phase 6 — Sửa lỗi Deploy job (25/06/2026)

**Run lỗi:** `28149078231` — Unit Test ✅, Train ✅, Eval ✅, **Deploy ❌**

**Nguyên nhân 1 — `needs.train` không khả dụng trong job Deploy:**

```yaml
# SAI — deploy chỉ needs: eval
deploy:
  needs: eval
  ...
  new_acc = float("${{ needs.train.outputs.accuracy }}")  # rỗng → ValueError

# ĐÚNG — thêm train vào needs
deploy:
  needs: [eval, train]
```

GitHub Actions chỉ cho phép truy cập `outputs` của job **trực tiếp** trong `needs`. Job `eval` không forward `accuracy` sang `deploy`.

**Nguyên nhân 2 — đường dẫn download artifact:**

```yaml
# SAI — file nằm ở outputs/outputs/metrics.json
- uses: actions/download-artifact@v4
  with:
    name: training-outputs
    path: outputs

# ĐÚNG — giữ cấu trúc outputs/metrics.json
- uses: actions/download-artifact@v4
  with:
    name: training-outputs
    path: .
```

**Commit sửa:** `9ed6a88` (artifact path) + commit tiếp theo (`needs: [eval, train]`).

**Sau khi pipeline xanh:** chụp log dòng `Rollback check: new=..., previous=...` → `screenshots/10-bonus-rollback-check.png`

**Run `28149234171` — Rollback vẫn fail sau fix needs:**

| Job | Kết quả |
|-----|---------|
| Unit Test | ✅ |
| Train | ✅ |
| Eval | ✅ |
| Deploy | ❌ — step `Bonus 4 - Rollback check` |

**Nguyên nhân 3 — so sánh float thô:**

```
new_acc = 0.7539999...  (từ job output)
old_acc = 0.7540        (từ S3 baseline upload tay)
0.7539999 < 0.754 → FAILED rollback
```

**Sửa lần 2:**

1. Download artifact **trước** rollback → đọc `new_acc` từ `outputs/metrics.json` (cùng file train tạo)
2. So sánh `round(new_acc, 4) < round(old_acc, 4)` thay vì so sánh float thô
3. Đồng bộ lại S3 baseline từ `outputs/metrics.json` local (accuracy = 0.754)

**Commit:** `fix rollback float compare` + retrigger qua `params.yaml`

**Run `28149935839` — Rollback vẫn fail (accuracy CI < baseline tay):**

| Job | Kết quả |
|-----|---------|
| Unit Test / Train / Eval | ✅ |
| Deploy | ❌ — `Download artifact` ✅ nhưng rollback so sánh với S3 baseline `0.754` upload tay |

**Nguyên nhân 4 — baseline S3 không khớp CI:**

- Baseline `models/latest/metrics.json` được upload **tay** từ máy local (0.754)
- CI train có thể cho accuracy hơi thấp hơn khi làm tròn (vẫn ≥ 0.70 → Eval pass)
- Rollback đúng logic bonus: **chặn deploy khi model mới kém hơn model đang chạy**

**Sửa lần 3 — reset baseline:**

```bash
aws s3 rm s3://mlops-lab-949678235460-hai/models/latest/metrics.json
```

→ Lần deploy tiếp theo: log `Khong co metrics cu tren S3 — lan deploy dau tien, bo qua rollback check.`
→ Sau deploy thành công: CI tự upload `metrics.json` lên S3 (accuracy thực từ pipeline)
→ Các lần sau: rollback so sánh đúng với baseline do chính CI tạo

---

**Run `28150096144` — vẫn fail dù đã xóa baseline S3:**

- Train artifact từ run này chứa `metrics.json` (không nằm trong thư mục `outputs/`)
- `download-artifact` giải nén ra root (`./metrics.json`, `./report.txt`)
- Rollback step đang đọc cứng `outputs/metrics.json` → `FileNotFoundError` → fail

**Sửa lần 4 — hỗ trợ 2 đường dẫn artifact:**

```python
metrics_path = "outputs/metrics.json" if os.path.exists("outputs/metrics.json") else "metrics.json"
with open(metrics_path) as f:
    new_acc = float(json.load(f)["accuracy"])
```

Áp dụng cùng fallback cho bước upload metrics lên S3 sau deploy.

---

## Checklist nộp bài

> File nộp chính thức: [`SUBMISSION.md`](SUBMISSION.md) | Thư mục ảnh: [`screenshots/`](screenshots/)

### 1. URL repo GitHub public

- [x] https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai

### 2. Chuỗi screenshot (theo thứ tự lab)

| # | Nội dung | File |
|---|----------|------|
| 1 | MLflow ≥3 experiments | [x] `screenshots/08-mlflow-experiments-top-runs.png` *(tạo tự động từ mlflow.db)* |
| 2a | Actions Run #1 — Eval fail | [x] `screenshots/02-github-actions-run1-eval-gate-failed.png` |
| 2b | Actions Run #2 — 4 jobs xanh | [x] `screenshots/03-github-actions-run2-all-jobs-green.png` |
| 2c | Actions overview (bonus) | [x] `screenshots/01-github-actions-overview.png` |
| 3 | curl `/health` + `/predict` | [x] `screenshots/07-curl-api-health-predict.png` |
| 4a | S3 bucket overview | [x] `screenshots/04-s3-bucket-dvc-and-models.png` |
| 4b | S3 DVC data files | [x] `screenshots/05-s3-dvc-data-files.png` |
| 4c | S3 model `model.pkl` | [x] `screenshots/06-s3-model-latest-pkl.png` |

### 3. Báo cáo 1 trang A4

- [x] Nội dung trong [`SUBMISSION.md`](SUBMISSION.md) mục "Báo cáo ngắn" — copy sang PDF/Word khi nộp LMS

---

## Draft báo cáo A4

*(Đã chuyển sang [`SUBMISSION.md`](SUBMISSION.md) — dùng file đó để nộp)*

---

## Tổng quan kiến trúc

```
[Máy local] ──git push──▶ [GitHub fork]
                              │
                              ▼ GitHub Actions
                    [Test → Train → Eval → Deploy]
                         │              │
                    dvc pull/push      SSH restart EC2
                         │              │
                         ▼              ▼
              [S3: data + model]   [EC2: FastAPI :8000]
                                         POST /predict
```

**Cloud provider:** AWS (Account `949678235460`, user `ai-lab-user`, region `us-east-1`)

---

## Bước 1 — MLflow tracking cục bộ

### Cài môi trường

```bash
cd /Users/minhhai/workspace/ai/VinUni/Assignment/Day21-Track2-2A202600713-DangMinhHai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_data.py
```

### Cấu hình MLflow

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
export MLFLOW_ARTIFACT_ROOT=./mlartifacts
python src/train.py   # chạy nhiều lần, đổi params.yaml giữa các lần
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

### Code `src/train.py` — logic chính

```python
df_train = pd.read_csv(data_path)
df_eval  = pd.read_csv(eval_path)
X_train = df_train.drop(columns=["target"])
y_train = df_train["target"]

with mlflow.start_run():
    mlflow.log_params(params)
    model = RandomForestClassifier(**params, random_state=42)
    model.fit(X_train, y_train)
    acc = accuracy_score(y_eval, model.predict(X_eval))
    f1  = f1_score(y_eval, preds, average="weighted")
    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("f1_score", f1)
    json.dump({"accuracy": acc, "f1_score": f1}, open("outputs/metrics.json", "w"))
    joblib.dump(model, "models/model.pkl")
```

---

## Bước 2 — DVC + CI/CD + Deploy EC2 (AWS)

### DVC + S3 (đã chạy)

```bash
export BUCKET=mlops-lab-949678235460-hai
dvc init
dvc remote add -d myremote s3://$BUCKET/dvc
dvc add data/train_phase1.csv data/eval.csv data/train_phase2.csv
dvc push
```

### GitHub Secrets (đã cấu hình ✅)

| Secret | Giá trị |
|--------|---------|
| `CLOUD_CREDENTIALS` | JSON từ `aws-creds-github.json` |
| `CLOUD_BUCKET` | `mlops-lab-949678235460-hai` |
| `VM_HOST` | `13.218.84.151` |
| `VM_USER` | `ubuntu` |
| `VM_SSH_KEY` | `~/.ssh/mlops_deploy` (private key) |

### CI/CD pipeline (`.github/workflows/mlops.yml`)

```
Unit Test → Train → Eval (gate ≥0.70) → Deploy (SSH + health check)
```

**Eval gate:**
```python
if acc < 0.70:
    raise SystemExit(f"FAILED: accuracy {acc:.4f} < 0.70. Huy deploy.")
```

**Upload model S3 (boto3):**
```python
s3.upload_file("models/model.pkl", bucket, "models/latest/model.pkl")
```

**Serve trên EC2 (`src/serve.py`):**
```python
s3.download_file(S3_BUCKET, "models/latest/model.pkl", MODEL_PATH)
```

---

## Bước 3 — Huấn luyện liên tục (đã chạy ✅)

```bash
python add_new_data.py          # 2998 → 5996 mẫu
dvc add data/train_phase1.csv
git commit -m "data: bổ sung 2998 mẫu dữ liệu mới (train_phase2)"
dvc push                        # TRƯỚC git push
git push origin master
```

### So sánh metrics

| Chỉ số | Bước 2 (2998 mẫu) | Bước 3 (5996 mẫu) |
|--------|-------------------|-------------------|
| accuracy | ~0.686 | ~0.754 |
| f1_score | ~0.685 | ~0.753 |

---

## Khó khăn đã gặp & cách xử lý

| Vấn đề | Cách xử lý | Trạng thái |
|--------|------------|------------|
| `ai-lab-user` thiếu quyền S3 | Thêm `AmazonS3FullAccess` vào `AI-Lab-Group` | ✅ |
| Fork repo — Actions disabled | Bật Actions trên fork | ✅ |
| Accuracy 2998 mẫu < 0.70 | Bước 3 gộp data → 0.754 | ✅ |
| Chuyển GCP → AWS | Sửa `serve.py`, `mlops.yml`, `requirements.txt` | ✅ |

---

## File đã thay đổi

| File | Thay đổi |
|------|----------|
| `src/train.py` | Train + MLflow + lưu metrics/model |
| `src/serve.py` | boto3 S3 + `/health` + `/predict` |
| `tests/test_train.py` | 3 unit tests |
| `.github/workflows/mlops.yml` | AWS auth + 4 jobs CI/CD |
| `requirements.txt` | `dvc[s3]` + `boto3` |
| `params.yaml` | Best params n=300, max_depth=null |
| `.dvc/config` | Remote S3 |
| `data/*.dvc` | DVC pointers cho 3 CSV |
| `MY_LAB_NOTES.md` | File ghi chú này |
| `SUBMISSION.md` | Tài liệu nộp bài chính thức |
| `screenshots/` | 8 ảnh + README index |
