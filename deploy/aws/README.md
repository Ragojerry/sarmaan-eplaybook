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

## Ask assistant and reference library

`/ai/ask` uses the same keyword engine the phones run offline, over the training
modules first and, only when they have no answer, the approved documents in the
admin portal's Reference library. Reference documents (PDF, .docx, text; 10 MB
max) are stored in Postgres (`reference_documents`, original file included), so
they are covered by database backups and never touched by a redeploy. Phones that
are online ask the server first (8 s limit), then answer on the device.

Curated answers (admin portal > Curated answers, table `faq_entries`) are checked
before everything else, on the server and on phones. Approved answers are live
online at once; they reach phones as extra passages (`faq_questions` set) in the
next release package or content sync.

The first-launch consent screen's text (admin portal > Consent text, table
`consent_texts`) is per language; `GET /consent` is public because the screen
comes before login. Phones cache all languages when they open the language
screen online and fall back to English, then to the copy built into the app.

## Learner roles and pre/post tests

Backend migration `a3c8e4f61b29` (see docs/roles-and-tests.md) adds learner
roles, module audiences and the pre-test/post-test flow. The minimum app version
for the new flow is **0.1.8**: older apps keep syncing and receive only their
role's content, but cannot complete modules that have questions. Before turning
it on, confirm the module audiences and flagged accounts on the portal's "Roles &
tests" page, and update learners' phones. To roll back, restore the pre-deploy
dump or run `alembic downgrade f5b3d9e1a246`, which loses learner roles and
audiences.

A 100% pre-test is auto-approved by a post-test at or above
`POST_TEST_AUTO_APPROVE_PERCENT`, default 90. To change the threshold, set it in
`/opt/sarmaan/.env.prod` and restart the backend container.

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
| 0.1.5 | 2026-11-04 | `c4960daaaa52ed9529c803b9e56e9db23835cd9e44f0b120c8cb20dd973bef54` |
| 0.1.6 | 2026-11-04 | `abbaff3a3b34916624e728b42979af542e707f0b703f025d691cdbc7038e2e23` |
| 0.1.7 | 2026-11-04 | `3b2c2eb4201f8546ad83022271c16b1bb904d8cc2c86498c6d5dcaa5d2c0f54d` |
| 0.1.8 | 2026-11-04 | `3ec1b325650d0f9f5de98ec3629fee9ba2fc8e0d09cfaff0e8aad5bc4d1aca09` |
| 0.1.9 | 2026-11-05 | `bb16973a94adee49f37d58202bc8d5291f6d9b1b016614a38d7102fe4bb02b1d` |
| 0.1.10 | 2026-11-06 | `6d29e5838fa2be0061aaf0958c8278e46352653a5f5a17c7274bcac6c6b3e430` |
