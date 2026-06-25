# Lab Notes - MLOps CI/CD (Day 21)

> File ghi chú cá nhân của **Đặng Minh Hải** — lưu lại từng bước làm bài, lý do và mục đích.
> Repo: `git@github.com:minhhai203/Day21-Track2-2A202600713-DangMinhHai.git`

---

## Tổng quan bài lab

| Bước | Mục tiêu | Rubric |
|------|----------|--------|
| **1** | MLflow tracking cục bộ, chạy ≥3 thí nghiệm, chọn hyperparams tốt nhất | 24 điểm |
| **2** | DVC + GitHub Actions (Test → Train → Eval → Deploy) + FastAPI trên VM | 44 điểm |
| **3** | Thêm dữ liệu mới → pipeline tự chạy lại | 12 điểm |

**Kiến trúc:** Push code/data → GitHub Actions → DVC pull từ Cloud Storage → Train → Eval gate (≥0.70) → Deploy lên VM → FastAPI `/predict`.

---

## Trạng thái hiện tại (AI đã làm)

- [x] Implement toàn bộ code: `src/train.py`, `src/serve.py`, `tests/test_train.py`, `.github/workflows/mlops.yml`
- [x] Tạo `src/__init__.py`, `tests/__init__.py`
- [x] Cài venv, `pip install -r requirements.txt`, `python generate_data.py`
- [x] Chạy ≥3 thí nghiệm MLflow, chọn params tốt nhất
- [x] `pytest tests/ -v` — **3/3 passed**
- [ ] **Bạn cần làm:** AWS S3 + EC2 setup, DVC, GitHub Secrets, push code, chụp màn hình nộp bài

> **Cloud provider:** AWS (Account `949678235460`, user `ai-lab-user`, region `us-east-1`)

---

## Bước 1 — MLflow tracking cục bộ

### 1.1 Tại sao cần bước này?

Bước 1 xây nền tảng **experiment tracking**: mọi lần huấn luyện đều ghi lại params, metrics, model artifact. Đây là thói quen MLOps cơ bản trước khi tự động hóa CI/CD.

### 1.2 Cài môi trường (đã chạy)

```bash
cd /Users/minhhai/workspace/ai/VinUni/Assignment/Day21-Track2-2A202600713-DangMinhHai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_data.py
```

**Mục đích:** Tạo 3 file CSV (2998 / 500 / 2998 mẫu) từ dataset Wine Quality UCI.

### 1.3 Cấu hình MLflow

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
export MLFLOW_ARTIFACT_ROOT=./mlartifacts
```

**Mục đích:** Lưu experiment vào SQLite cục bộ, không cần server riêng.

### 1.4 Code `src/train.py` — logic chính

```python
# Đọc data → tách X/y → MLflow run → train RandomForest → log metrics → lưu file
df_train = pd.read_csv(data_path)
df_eval  = pd.read_csv(eval_path)
X_train = df_train.drop(columns=["target"])
y_train = df_train["target"]
# ... train, predict, log accuracy + f1_score ...
json.dump({"accuracy": acc, "f1_score": f1}, open("outputs/metrics.json", "w"))
joblib.dump(model, "models/model.pkl")
```

**Mục đích từng output:**
- `outputs/metrics.json` → GitHub Actions đọc accuracy cho eval gate
- `models/model.pkl` → upload lên S3, EC2 tải về serve
- MLflow UI → chụp màn hình nộp bài

### 1.5 Ba thí nghiệm đã chạy

| Run | n_estimators | max_depth | min_samples_split | Accuracy | F1 |
|-----|-------------|-----------|-------------------|----------|-----|
| 1 | 100 | 5 | 2 | 0.5640 | 0.5534 |
| 2 | 50 | 3 | 2 | 0.5580 | 0.5185 |
| 3 | 200 | 10 | 5 | 0.6420 | 0.6394 |

Thêm các run thử nghiệm → best trên **2998 mẫu**: `n_estimators=300, max_depth=null` → **accuracy 0.686**

### 1.6 Params đã chọn cho Bước 2+ (`params.yaml`)

```yaml
n_estimators: 300
max_depth: null
min_samples_split: 2
```

**Lý do chọn:** Accuracy cao nhất trong các combo đã thử trên tập 2998 mẫu. Sau khi gộp thêm dữ liệu (Bước 3), cùng bộ params đạt **0.754** — vượt ngưỡng 0.70.

> **Lưu ý quan trọng:** Với chỉ 2998 mẫu huấn luyện, accuracy ~0.686 **dưới ngưỡng 0.70** → job **Eval sẽ chặn Deploy** ở lần chạy pipeline đầu. Đây vẫn đúng hành vi eval gate (rubric 4 điểm). Để cả 4 jobs xanh, cần Bước 3 (thêm data) hoặc xem mục "Chiến lược pipeline" bên dưới.

### 1.7 Xem MLflow UI — **BẠN CẦN LÀM**

```bash
source .venv/bin/activate
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Mở http://localhost:5000 → **chụp màn hình** ≥3 runs (nộp bài).

---

## Bước 2 — DVC + CI/CD + Deploy EC2 (AWS)

### 2.1 Tại sao cần DVC?

Git không phù hợp lưu file CSV lớn. DVC tạo file `.dvc` (con trỏ) commit vào Git, còn data thật nằm trên **S3** → reproducible + versioned data.

### 2.2 AWS CLI — đã sẵn sàng

```bash
aws --version
aws sts get-caller-identity
# Account: 949678235460 | User: ai-lab-user | Region: us-east-1
```

### 2.3 Cấp quyền IAM — **BẠN CẦN LÀM TRƯỚC**

User `ai-lab-user` hiện **chưa có quyền S3** (`AccessDenied` khi tạo bucket).

Vào **AWS Console → IAM → Users → ai-lab-user → Add permissions**, attach policy (hoặc tạo inline policy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket", "s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-lab-*",
        "arn:aws:s3:::mlops-lab-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances", "ec2:DescribeInstances", "ec2:TerminateInstances",
        "ec2:CreateSecurityGroup", "ec2:AuthorizeSecurityGroupIngress",
        "ec2:DescribeSecurityGroups", "ec2:CreateKeyPair", "ec2:ImportKeyPair"
      ],
      "Resource": "*"
    }
  ]
}
```

> Nếu dùng tài khoản root/admin: có thể attach `AmazonS3FullAccess` + `AmazonEC2FullAccess` cho nhanh (lab only).

### 2.4 Tạo S3 Bucket — **BẠN CẦN LÀM**

```bash
export BUCKET=mlops-lab-949678235460-hai   # đổi tên nếu đã tồn tại
export AWS_DEFAULT_REGION=us-east-1

aws s3 mb s3://$BUCKET --region us-east-1
aws s3 ls   # xác nhận bucket đã tạo
```

**Mục đích:** Bucket lưu data DVC (`dvc/`) và model (`models/latest/model.pkl`).

### 2.5 Tạo Access Key cho GitHub Actions — **BẠN CẦN LÀM**

DVC local dùng credentials từ `~/.aws/credentials` (đã có). GitHub Actions cần key riêng:

1. **IAM → Users → ai-lab-user → Security credentials → Create access key**
2. Chọn "Application running outside AWS"
3. Lưu `Access key ID` và `Secret access key`

Tạo file local (không commit):

```bash
cat > aws-creds.json <<'EOF'
{
  "aws_access_key_id": "AKIA...",
  "aws_secret_access_key": "..."
}
EOF
```

**Mục đích:** GitHub Secret `CLOUD_CREDENTIALS` = toàn bộ nội dung JSON trên.

### 2.6 Khởi tạo DVC — **BẠN CẦN LÀM**

DVC S3 tự đọc `~/.aws/credentials` — không cần file key riêng như GCP.

```bash
source .venv/bin/activate
pip install -r requirements.txt   # dvc[s3] + boto3

dvc init
dvc remote add -d myremote s3://$BUCKET/dvc

dvc add data/train_phase1.csv
dvc add data/eval.csv
dvc add data/train_phase2.csv

git add data/*.dvc .dvc/config .gitignore
git commit -m "feat: track datasets with DVC"

dvc push   # đẩy CSV lên S3
```

Kiểm tra trên S3 Console: bucket → prefix `dvc/`.

### 2.7 Tạo EC2 instance — **BẠN CẦN LÀM**

**Cách 1 — AWS Console (dễ nhất):**

1. EC2 → Launch instance
2. Name: `mlops-serve`
3. AMI: **Ubuntu 22.04 LTS**
4. Instance type: **t2.micro** (free tier)
5. Key pair: tạo mới `mlops-serve-key.pem` (tải về!)
6. Security group: mở **SSH (22)** và **Custom TCP 8000**
7. Launch → lấy **Public IPv4 address** → ghi làm `VM_IP`

**Cách 2 — CLI:**

```bash
# Tạo key pair
aws ec2 create-key-pair --key-name mlops-serve-key \
  --query 'KeyMaterial' --output text > mlops-serve-key.pem
chmod 400 mlops-serve-key.pem

# Security group
aws ec2 create-security-group --group-name mlops-serve-sg \
  --description "MLOps inference" --region us-east-1
# Ghi lại GroupId, rồi:
aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0

# Launch instance (Amazon Linux 2023 AMI id có thể khác — dùng Console nếu phức tạp)
```

### 2.8 Cấu hình EC2 (một lần) — **BẠN CẦN LÀM**

```bash
ssh -i mlops-serve-key.pem ubuntu@<VM_IP>

# Trên EC2:
sudo apt update && sudo apt install -y python3-pip
pip3 install fastapi uvicorn scikit-learn joblib boto3
mkdir -p ~/models ~/src ~/.aws
exit
```

Copy `serve.py` và AWS credentials lên EC2:

```bash
scp -i mlops-serve-key.pem src/serve.py ubuntu@<VM_IP>:~/src/serve.py

# Copy credentials (dùng profile hiện tại)
scp -i mlops-serve-key.pem ~/.aws/credentials ubuntu@<VM_IP>:~/.aws/credentials
```

**Tạo systemd service trên EC2** (thay `<YOUR_BUCKET_NAME>`):

```bash
ssh -i mlops-serve-key.pem ubuntu@<VM_IP>
```

```bash
sudo tee /etc/systemd/system/mlops-serve.service > /dev/null <<EOF
[Unit]
Description=MLOps Model Inference Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="S3_BUCKET=<YOUR_BUCKET_NAME>"
Environment="AWS_DEFAULT_REGION=us-east-1"
Environment="AWS_SHARED_CREDENTIALS_FILE=/home/ubuntu/.aws/credentials"
ExecStart=/usr/bin/python3 /home/ubuntu/src/serve.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mlops-serve
exit
```

**Mục đích:** Server tự khởi động lại sau reboot; tải model từ S3 khi start.

### 2.9 SSH key cho GitHub Actions — **BẠN CẦN LÀM**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mlops_deploy -N "" -C "github-actions-deploy"

ssh -i mlops-serve-key.pem ubuntu@<VM_IP> \
  "echo '$(cat ~/.ssh/mlops_deploy.pub)' >> ~/.ssh/authorized_keys"
```

## Thông tin hạ tầng AWS (đã tạo)

| Resource | Giá trị |
|----------|---------|
| S3 Bucket | `mlops-lab-949678235460-hai` |
| EC2 Instance | `i-05bedc213d096de3e` (t2.micro, Ubuntu 22.04) |
| EC2 Public IP | `13.218.84.151` |
| Region | `us-east-1` |
| DVC remote | `s3://mlops-lab-949678235460-hai/dvc` |
| SSH key (local) | `mlops-serve-key.pem` (gitignored) |

DVC push: **3 files** đã lên S3 ✅  
EC2 systemd service: **enabled** (chưa start — chờ model trên S3 sau pipeline Train)

---

## GitHub Secrets — **BẠN CẦN LÀM NGAY** (trước khi pipeline chạy)

Vào: https://github.com/minhhai203/Day21-Track2-2A202600713-DangMinhHai/settings/secrets/actions

| Secret | Giá trị |
|--------|---------|
| `CLOUD_CREDENTIALS` | Copy từ file `aws-creds-github.json` (đã tạo ở thư mục project, gitignored) |
| `CLOUD_BUCKET` | `mlops-lab-949678235460-hai` |
| `VM_HOST` | `13.218.84.151` |
| `VM_USER` | `ubuntu` |
| `VM_SSH_KEY` | Copy toàn bộ nội dung file `~/.ssh/mlops_deploy` (private key) |

```bash
# Xem credentials cho secret CLOUD_CREDENTIALS:
cat aws-creds-github.json

# Xem private key cho secret VM_SSH_KEY:
cat ~/.ssh/mlops_deploy
```

---

Pipeline 4 jobs — auth qua `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, upload model bằng **boto3**:

```python
s3 = boto3.client("s3")
s3.upload_file("models/model.pkl", bucket, "models/latest/model.pkl")
```

`src/serve.py` tải model từ S3:

```python
s3 = boto3.client("s3")
s3.download_file(S3_BUCKET, "models/latest/model.pkl", MODEL_PATH)
```

### 2.12 Push code lên GitHub — **BẠN CẦN LÀM**

```bash
git add src/ tests/ .github/ params.yaml requirements.txt MY_LAB_NOTES.md
git commit -m "feat: AWS CI/CD pipeline with S3 and EC2"
git push origin master
```

Sau pipeline Train thành công (model đã lên S3):

```bash
ssh -i mlops-serve-key.pem ubuntu@<VM_IP> "sudo systemctl start mlops-serve"
```

### 2.13 Test API — **BẠN CẦN LÀM**

```bash
VM_IP=<YOUR_EC2_IP>

curl http://$VM_IP:8000/health
# Kỳ vọng: {"status":"ok"}

curl -X POST http://$VM_IP:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [7.4, 0.70, 0.00, 1.9, 0.076, 11.0, 34.0, 0.9978, 3.51, 0.56, 9.4, 0]}'
# Kỳ vọng: {"prediction":0,"label":"thap"}
```

**Chụp màn hình** curl + **S3 Console** (prefix `dvc/` và `models/latest/`).

---

## Chiến lược pipeline & ngưỡng 0.70

| Lần chạy | Dữ liệu train | Accuracy dự kiến | Eval gate | Deploy |
|----------|---------------|------------------|-----------|--------|
| Pipeline đầu (Bước 2) | 2998 mẫu | ~0.686 | ❌ Chặn | Không chạy |
| Sau Bước 3 | 5996 mẫu | ~0.754 | ✅ Pass | ✅ Chạy |

**Rubric eval gate (4đ):** Lần chạy đầu chứng minh deploy bị chặn khi accuracy < 0.70.

**Rubric CI/CD (16đ) + Serving (12đ):** Cần screenshot lần chạy **sau Bước 3** với cả 4 jobs xanh.

---

## Bước 3 — Huấn luyện liên tục (thêm dữ liệu)

### 3.1 Tại sao?

Mô phỏng production: data mới → version DVC → git push → pipeline tự retrain + redeploy.

### 3.2 Các bước — **BẠN CẦN LÀM**

```bash
source .venv/bin/activate
python add_new_data.py
# Kỳ vọng: Cap nhat du lieu: 2998 -> 5996 mau

dvc add data/train_phase1.csv
git add data/train_phase1.csv.dvc
git commit -m "data: bổ sung 2998 mẫu dữ liệu mới (train_phase2)"

dvc push          # QUAN TRỌNG: push data TRƯỚC git push
git push origin master
```

**Thứ tự `dvc push` trước `git push`:** Tránh CI pull data mới khi cloud chưa có file.

### 3.3 So sánh metrics (điền sau khi pipeline chạy xong)

| Chỉ số | Bước 2 (2998 mẫu) | Bước 3 (5996 mẫu) |
|--------|-------------------|-------------------|
| accuracy | ~0.686 | ~0.754 |
| f1_score | ~0.685 | ~0.753 |

Tải `metrics.json` từ **Artifacts** của job Train trên GitHub Actions để điền số chính xác.

---

## Checklist nộp bài

- [ ] URL repo GitHub public
- [ ] Screenshot MLflow UI (≥3 experiments)
- [ ] Screenshot GitHub Actions (4 jobs xanh — sau Bước 3)
- [ ] Screenshot `curl /health` và `curl /predict`
- [ ] Screenshot Cloud Storage (data `dvc/` + model `models/latest/`)
- [ ] Báo cáo 1 trang A4: params đã chọn + khó khăn & cách giải quyết

---

## Khó khăn dự kiến & cách xử lý

| Vấn đề | Cách xử lý |
|--------|------------|
| `AccessDenied` khi tạo S3 bucket | Cấp quyền IAM cho `ai-lab-user` (mục 2.3) |
| `dvc push` lỗi auth | Kiểm tra `aws sts get-caller-identity`, `~/.aws/credentials` |
| GitHub Actions `dvc pull` fail | Secret `CLOUD_CREDENTIALS` = JSON với `aws_access_key_id` + `aws_secret_access_key` |
| Eval gate chặn deploy | Bình thường với 2998 mẫu; làm Bước 3 để vượt 0.70 |
| Service EC2 không start | `sudo journalctl -u mlops-serve -n 50` — thường do model chưa có trên S3 |
| Pipeline không trigger | Push phải thay đổi `src/**.py`, `params.yaml`, hoặc `data/**.dvc` trên nhánh `master`/`main` |
| SSH vào EC2 fail | Kiểm tra Security Group port 22, key `.pem` permissions (`chmod 400`) |

---

## File đã thay đổi (so với template ban đầu)

| File | Thay đổi |
|------|----------|
| `src/train.py` | Hoàn thiện toàn bộ TODO — train + MLflow + lưu metrics/model |
| `src/serve.py` | boto3 download S3 + `/health` + `/predict` |
| `requirements.txt` | `dvc[s3]` + `boto3` (thay GCP) |
| `.github/workflows/mlops.yml` | AWS auth + boto3 upload S3 |
| `params.yaml` | Best params: n=300, max_depth=null |
| `.gitignore` | Thêm `mlruns/` |
| `src/__init__.py`, `tests/__init__.py` | Tạo mới |
