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

## Publish a test APK

Test builds are served from the admin bucket under `downloads/<random>/`, through
the admin CloudFront distribution. The bucket stays private (CloudFront can read
objects but not list them), so the random folder name is what keeps a link
unguessable: anyone who has the link can download, and it never expires. Bump
`version:` in `mobile/pubspec.yaml` first, and use a new file name per build.

```powershell
$tok = -join (1..24 | % { '{0:x}' -f (Get-Random -Maximum 16) })
$name = "sarmaan-eplaybook-<version>-<yyyymmdd>.apk"
aws s3 cp mobile/build/app/outputs/flutter-apk/app-release.apk "s3://sarmaan-admin-568898409880/downloads/$tok/$name" `
  --content-type application/vnd.android.package-archive `
  --content-disposition "attachment; filename=`"$name`"" --cache-control "public,max-age=3600"
# Link: https://dpoc28iz0vbai.cloudfront.net/downloads/$tok/$name
```

To withdraw a build, `aws s3 rm` it; CloudFront may serve a cached copy for up
to an hour. Never `aws s3 sync --delete` the admin bucket root: that would also
delete everything under `downloads/`.

Don't record the random folder names in this repo; they are the only thing
protecting the links. List published builds with
`aws s3 ls s3://sarmaan-admin-568898409880/downloads/ --recursive`.

| Version | Date | SHA-256 |
|---|---|---|
| 0.1.0 | 2026-10-30 | `6bdf2c4a31b980ff9578389954348c05755ab0dafd1a84804db36cbd36fdfcb6` |
| 0.1.1 | 2026-10-30 | `54bee08978c951b5b41931450c991cce1a14b921ea8394630dbb78417ec7b954` |
| 0.1.2 | 2026-11-03 | `278c8d848df6cd2777246c022df5a736409aa5ebbb260168ebdcf53c87c8d1a8` |
| 0.1.3 | 2026-11-03 | `d0e5f3c408e854b6bd53c7216dafcf25d4e709ac496882006c552a4532e3d1da` |
| 0.1.4 | 2026-11-03 | `26c2076bc988004d424e300cd98970a245769427add80aefe5fc54e230344b97` |
