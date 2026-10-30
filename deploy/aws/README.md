# AWS deployment (project 568898409880, eu-north-1)

| Piece | Where |
|---|---|
| API (HTTPS) | https://d1eortf8qang6z.cloudfront.net — CloudFront `EHJ9GXES5P7D9` |
| Admin portal | https://dpoc28iz0vbai.cloudfront.net — CloudFront `E14XP9UETH7OVQ`, bucket `sarmaan-admin-568898409880` |
| Backend host | EC2 `i-00638b14a3196fd24` (t4g.small, AL2023), Elastic IP 13.49.203.71 |
| Deploy bucket | `sarmaan-deploy-568898409880` (bundle + bootstrap.sh) |
| Firewall | `sg-0c87f03ff2dbd255d`: port 80 from the CloudFront origin-facing prefix list only |
| Host access | Session Manager only (role `sarmaan-ec2-role`); no SSH, no key pair |

On the host the app lives in `/opt/sarmaan`; secrets are in `/opt/sarmaan/.env.prod`
(generated there, root-only). Postgres data is in the `sarmaan_db_data` Docker volume.

AWS CLI calls below assume `--profile sarmaan --region eu-north-1`.

## Redeploy the backend

From `sarmaan-eplaybook/` (never include `.venv` or `.env`):

```powershell
tar.exe -czf bundle.tar.gz --exclude=backend/.venv --exclude=backend/.env --exclude=backend/tests `
  --exclude=backend/.pytest_cache --exclude=__pycache__ --exclude=*.pyc backend content deploy/aws
aws s3 cp bundle.tar.gz s3://sarmaan-deploy-568898409880/bundle.tar.gz
aws s3 cp deploy/aws/bootstrap.sh s3://sarmaan-deploy-568898409880/bootstrap.sh
```

Then run `bootstrap.sh` on the host with SSM `AWS-RunShellScript`:

```
aws s3 cp s3://sarmaan-deploy-568898409880/bootstrap.sh /tmp/bootstrap.sh
bash /tmp/bootstrap.sh sarmaan-deploy-568898409880 '["https://dpoc28iz0vbai.cloudfront.net"]'
```

It keeps the existing secrets and database; it only restores `db.dump` into an
empty database. **Caution:** `content/` from the bundle overwrites the host's
copy. Once people upload media or publish releases on AWS, leave `content` out of
the bundle; otherwise a stale local package replaces the published one and phones
fail sync with a size/checksum mismatch.

## Redeploy the admin portal

```powershell
cd admin
$env:VITE_API_BASE_URL='https://d1eortf8qang6z.cloudfront.net'; npm run build
aws s3 sync dist/assets s3://sarmaan-admin-568898409880/assets --cache-control "public,max-age=31536000,immutable"
aws s3 cp dist/index.html s3://sarmaan-admin-568898409880/index.html --cache-control no-cache
```

## Mobile builds against AWS

```
flutter build apk --release --dart-define=API_BASE_URL=https://d1eortf8qang6z.cloudfront.net
```

Without `--dart-define` the app talks to the local dev backend (`10.0.2.2:8000`).
