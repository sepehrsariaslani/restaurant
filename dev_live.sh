#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  dev_live.sh — بازسازی کامل استک زنده بعد از ریست سندباکس
#  (سندباکس فقط ریپو restaurant را نگه می‌دارد؛ بقیه هر بار پاک می‌شود.)
#
#  اجرا:  bash /home/user/restaurant/dev_live.sh
#  بعدش:  سرویس‌ها را با start_process بالا بیاور (فرانت 5000 + بک‌اند 8000)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO=/home/user/restaurant
LOG_DIR=/home/user/logs
mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_DIR/rebuild.log") 2>&1

echo "===== [1/9] ابزارها: venv + bench + uv ====="
[ -d /home/user/frappe-venv ] || python3 -m venv /home/user/frappe-venv
/home/user/frappe-venv/bin/pip install --quiet --upgrade pip
/home/user/frappe-venv/bin/pip install --quiet frappe-bench uv

echo "===== [2/9] Redis (redislite) ====="
[ -d /home/user/redislite-venv ] || python3 -m venv /home/user/redislite-venv
/home/user/redislite-venv/bin/pip install --quiet redislite
sudo ln -sf /home/user/redislite-venv/lib/python3.11/site-packages/redislite/bin/redis-server /usr/local/bin/redis-server
redis-server --daemonize yes --bind 127.0.0.1 --port 11000 --save "" --appendonly no || true
redis-server --daemonize yes --bind 127.0.0.1 --port 13000 --save "" --appendonly no || true

echo "===== [3/9] PostgreSQL (PGlite) ====="
mkdir -p /home/user/pgserver
cd /home/user/pgserver
[ -d node_modules ] || npm install @electric-sql/pglite @electric-sql/pglite-socket
pgrep -f pglite-server >/dev/null || {
  nohup ./node_modules/.bin/pglite-server --db=/home/user/pgdata --port=5432 --host=127.0.0.1 --max-connections=10 >> "$LOG_DIR/pglite.log" 2>&1 &
}
for i in $(seq 1 30); do (exec 3<>/dev/tcp/127.0.0.1/5432) 2>/dev/null && break; sleep 1; done
echo "  pg up"

echo "===== [4/9] bench + frappe v15 (پچ yarn) ====="
export PATH="/home/user/frappe-venv/bin:/home/user/bin:$PATH"
# پچ bench: در هنگام init نباید yarn install را اجرا کند (شبکه ناپایدار است)
python3 - <<'PY'
p = "/home/user/frappe-venv/lib/python3.11/site-packages/bench/app.py"
s = open(p).read()
old = '\tif not using_cached and os.path.exists(os.path.join(app_path, "package.json")):\n\t\tyarn_install = "yarn install --check-files"'
new = '\tif (\n\t\tnot using_cached\n\t\tand not skip_assets\n\t\tand os.path.exists(os.path.join(app_path, "package.json"))\n\t):\n\t\tyarn_install = "yarn install --check-files"'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new))
    print("  bench patched")
PY
[ -d /home/user/bench ] || {
  cd /home/user
  /home/user/frappe-venv/bin/bench init --frappe-branch version-15 --skip-assets --no-procfile --no-backups /home/user/bench
}

echo "===== [5/9] اپ‌ها ====="
ln -sfn "$REPO" /home/user/bench/apps/restaurant
printf 'frappe\npayments\nerpnext\nrestaurant\n' > /home/user/bench/apps.txt
printf 'frappe\npayments\nerpnext\nrestaurant\n' > /home/user/bench/sites/apps.txt
cd /home/user/bench
env/bin/pip install --quiet -e "$REPO" || true
if [ ! -d apps/erpnext/.git ]; then
  /home/user/frappe-venv/bin/bench get-app --branch version-15 --skip-assets https://github.com/frappe/payments || true
  /home/user/frappe-venv/bin/bench get-app --branch version-15 --skip-assets https://github.com/frappe/erpnext || true
  env/bin/pip install --quiet -e apps/payments -e apps/erpnext || true
fi

echo "===== [6/9] psql شیم + پچ‌های frappe ====="
mkdir -p /home/user/bin
cat > /home/user/bin/psql <<'PY'
#!/home/user/bench/env/bin/python
import sys, re
try:
    import psycopg2
except ImportError:
    sys.exit(127)
uri = None; sql_file = None
args = sys.argv[1:]; i = 0
while i < len(args):
    a = args[i]
    if a.startswith("postgres://") or a.startswith("postgresql://"):
        uri = a
    elif a in ("-f", "--file") and i + 1 < len(args):
        sql_file = args[i + 1]; i += 1
    elif a.startswith("-") and "=" not in a and i + 1 < len(args) and not args[i + 1].startswith("-"):
        i += 1
    i += 1
if not uri:
    sys.exit(2)
m = re.match(r"postgres(?:ql)?://(?:([^:@/]+)(?::([^@/]*))?@)?([^:/@]+)(?::(\d+))?/([^?]+)", uri)
user, password, host, port, dbname = m.groups()
user = user or "postgres"; password = password or ""; host = host or "127.0.0.1"
port = int(port or 5432); dbname = dbname or "postgres"
sql = open(sql_file).read() if sql_file else sys.stdin.read()
if not sql.strip(): sys.exit(0)
try:
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
    cur = conn.cursor(); cur.execute(sql); conn.commit(); conn.close()
except Exception as exc:
    print(f"psql shim error: {exc}", file=sys.stderr); sys.exit(1)
PY
chmod +x /home/user/bin/psql

python3 - <<'PY'
base = "/home/user/bench/apps/frappe/frappe"
# link_filters json (postgres)
p = f"{base}/core/doctype/doctype/doctype.py"
s = open(p).read()
old = '''\t\tlink_filters_value = docfield.get("link_filters")
\t\tif not link_filters_value:
\t\t\treturn

\t\ttry:
\t\t\tlink_filters = json.loads(link_filters_value)
\t\texcept (TypeError, ValueError):
\t\t\tfrappe.throw(
\t\t\t\t_("Invalid Link Filters for field {0}. Link Filters must be valid JSON.").format(
\t\t\t\t\tfrappe.bold(docfield.label or docfield.fieldname)
\t\t\t\t)
\t\t\t)'''
new = '''\t\tlink_filters_value = docfield.get("link_filters")
\t\tif not link_filters_value:
\t\t\treturn

\t\tif isinstance(link_filters_value, (list, dict)):
\t\t\tlink_filters = link_filters_value
\t\telse:
\t\t\ttry:
\t\t\t\tlink_filters = json.loads(link_filters_value)
\t\t\texcept (TypeError, ValueError):
\t\t\t\tfrappe.throw(
\t\t\t\t\t_("Invalid Link Filters for field {0}. Link Filters must be valid JSON.").format(
\t\t\t\t\t\tfrappe.bold(docfield.label or docfield.fieldname)
\t\t\t\t\t)
\t\t\t\t)'''
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  link_filters patched")
# bundled_assets
p = f"{base}/utils/jinja_globals.py"
s = open(p).read()
old = "\t\tbundled_assets = get_assets_json()\n\t\tif path.endswith"
new = "\t\tbundled_assets = get_assets_json() or {}\n\t\tif path.endswith"
if old in s:
    open(p, "w").write(s.replace(old, new)); print("  assets patched")
# cookies SameSite=None + Partitioned
p = f"{base}/auth.py"
s = open(p).read()
old = '''\t\tsamesite="Lax",
\t\tmax_age=None,
\t):
\t\tif not secure and hasattr(frappe.local, "request"):
\t\t\tsecure = frappe.local.request.scheme == "https"

\t\tself.cookies[key] = {
\t\t\t"value": value,
\t\t\t"expires": expires,
\t\t\t"secure": secure,
\t\t\t"httponly": httponly,
\t\t\t"samesite": samesite,
\t\t\t"max_age": max_age,
\t\t}'''
new = '''\t\tsamesite=None,
\t\tmax_age=None,
\t):
\t\tif samesite is None:
\t\t\tsamesite = frappe.conf.get("cookie_samesite") or "Lax"
\t\tif not secure and hasattr(frappe.local, "request"):
\t\t\tsecure = frappe.local.request.scheme == "https"
\t\tpartitioned = False
\t\tif str(samesite).lower() == "none":
\t\t\tsamesite = "None"
\t\t\tsecure = True
\t\t\tpartitioned = True

\t\tself.cookies[key] = {
\t\t\t"value": value,
\t\t\t"expires": expires,
\t\t\t"secure": secure,
\t\t\t"httponly": httponly,
\t\t\t"samesite": samesite,
\t\t\t"max_age": max_age,
\t\t\t"partitioned": partitioned,
\t\t}'''
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  cookies patched")
# login response includes sid (sandbox iframe fallback)
p = f"{base}/auth.py"
s = open(p).read()
old = '\t\tif not resume:\n\t\t\tfrappe.response["full_name"] = self.full_name\n'
new = '\t\tif not resume:\n\t\t\tfrappe.response["full_name"] = self.full_name\n\t\t\tfrappe.response["sid"] = frappe.session.sid\n'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  login-sid patched")
# erpnext variant query: ORDER BY NULL -> ORDER BY t1.parent (postgres fix)
p = f"{base}/../../erpnext/erpnext/utilities/product.py"
s = open(p).read()
old = '\t\t\tGROUP BY\n\t\t\t\tt1.parent\n\t\t\tORDER BY\n\t\t\t\tNULL'
new = '\t\t\tGROUP BY\n\t\t\t\tt1.parent\n\t\t\tORDER BY\n\t\t\t\tt1.parent'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  variant-order patched")
# erpnext payment ledger postgres groupby fix
p = f"{base}/../../erpnext/erpnext/accounts/utils.py"
s = open(p).read()
old = '\t\t\t.groupby(ple.voucher_type, ple.voucher_no, ple.party_type, ple.party)\n\t\t)'
new = '\t\t\t.groupby(\n\t\t\t\tple.account, ple.voucher_type, ple.voucher_no, ple.party_type, ple.party,\n\t\t\t\tple.posting_date, ple.due_date, ple.account_currency, ple.cost_center, ple.remarks,\n\t\t\t)\n\t\t)'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  ple-groupby patched")
old = '\t\t\t.groupby(ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party)\n\t\t)'
new = '\t\t\t.groupby(\n\t\t\t\tple.account, ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party,\n\t\t\t\tple.posting_date, ple.due_date, ple.account_currency, ple.cost_center, ple.remarks,\n\t\t\t)\n\t\t)'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  ple-groupby2 patched")
# dev_auto_login: act as Administrator without credentials
p = f"{base}/sessions.py"
s = open(p).read()
old = '\tdef get_session_data(self):\n\t\tif self.sid == "Guest":\n\t\t\treturn frappe._dict({"user": "Guest"})'
new = '\tdef get_session_data(self):\n\t\tif self.sid == "Guest":\n\t\t\tif frappe.conf.get("dev_auto_login"):\n\t\t\t\treturn frappe._dict({"user": "Administrator"})\n\t\t\treturn frappe._dict({"user": "Guest"})'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  dev_auto_login patched")
# dev_auto_login: whitelist check ignores Guest so no "not whitelisted" errors
p = f"{base}/__init__.py"
s = open(p).read()
old = '\tis_guest = session["user"] == "Guest"\n\tif method not in whitelisted or (is_guest and method not in guest_methods):'
new = '\tis_guest = session["user"] == "Guest" and not frappe.conf.get("dev_auto_login")\n\tif method not in whitelisted or (is_guest and method not in guest_methods):'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  whitelist-guest patched")
PY

echo "===== [7/9] ساخت سایت + نصب اپ‌ها ====="
export PATH="/home/user/frappe-venv/bin:/home/user/bin:$PATH"
cd /home/user/bench
if [ ! -f sites/site1.local/site_config.json ]; then
  /home/user/frappe-venv/bin/bench new-site site1.local --db-type postgres --no-setup-db --admin-password admin \
    --db-name postgres --db-password postgres --db-host 127.0.0.1 --db-port 5432 \
    --db-root-username postgres --db-root-password postgres
fi
bench --site site1.local install-app payments erpnext restaurant || true
bench --site site1.local migrate || true
python3 - <<'PY'
import json
p = "/home/user/bench/sites/site1.local/site_config.json"
cfg = json.load(open(p))
cfg["developer_mode"] = 1
cfg["cookie_samesite"] = "none"
cfg["dev_auto_login"] = 1
cfg["ignore_csrf"] = 1
json.dump(cfg, open(p, "w"), indent=1)
print("  site_config set")
PY

# ── پچ‌های erpnext دوباره (install-app/migrate ممکن است فایل‌ها را برگرداند) ──
python3 - <<'PY'
# variant query: ORDER BY NULL -> ORDER BY t1.parent (postgres fix)
p = "/home/user/bench/apps/erpnext/erpnext/utilities/product.py"
s = open(p).read()
old = '\t\t\tGROUP BY\n\t\t\t\tt1.parent\n\t\t\tORDER BY\n\t\t\t\tNULL'
new = '\t\t\tGROUP BY\n\t\t\t\tt1.parent\n\t\t\tORDER BY\n\t\t\t\tt1.parent'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  variant-order re-patched")
# payment ledger postgres groupby fixes
p = "/home/user/bench/apps/erpnext/erpnext/accounts/utils.py"
s = open(p).read()
old = '\t\t\t.groupby(ple.voucher_type, ple.voucher_no, ple.party_type, ple.party)\n\t\t)'
new = '\t\t\t.groupby(\n\t\t\t\tple.account, ple.voucher_type, ple.voucher_no, ple.party_type, ple.party,\n\t\t\t\tple.posting_date, ple.due_date, ple.account_currency, ple.cost_center, ple.remarks,\n\t\t\t)\n\t\t)'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  ple-groupby re-patched")
old = '\t\t\t.groupby(ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party)\n\t\t)'
new = '\t\t\t.groupby(\n\t\t\t\tple.account, ple.against_voucher_type, ple.against_voucher_no, ple.party_type, ple.party,\n\t\t\t\tple.posting_date, ple.due_date, ple.account_currency, ple.cost_center, ple.remarks,\n\t\t\t)\n\t\t)'
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  ple-groupby2 re-patched")
# HAVING on alias -> WHERE on CTE column (postgres fix)
old = '''\t\tif self.get_invoices:
\t\t\tself.cte_query_voucher_amount_and_outstanding = (
\t\t\t\tself.cte_query_voucher_amount_and_outstanding.having(
\t\t\t\t\tqb.Field("outstanding_in_account_currency") > 0
\t\t\t\t)
\t\t\t)
\t\t# only fetch payments
\t\telif self.get_payments:
\t\t\tself.cte_query_voucher_amount_and_outstanding = (
\t\t\t\tself.cte_query_voucher_amount_and_outstanding.having(
\t\t\t\t\tqb.Field("outstanding_in_account_currency") < 0
\t\t\t\t)
\t\t\t)'''
new = '''\t\tif self.get_invoices:
\t\t\tself.cte_query_voucher_amount_and_outstanding = (
\t\t\t\tself.cte_query_voucher_amount_and_outstanding.where(
\t\t\t\t\tTable("outstanding").amount_in_account_currency > 0
\t\t\t\t)
\t\t\t)
\t\t# only fetch payments
\t\telif self.get_payments:
\t\t\tself.cte_query_voucher_amount_and_outstanding = (
\t\t\t\tself.cte_query_voucher_amount_and_outstanding.where(
\t\t\t\t\tTable("outstanding").amount_in_account_currency < 0
\t\t\t\t)
\t\t\t)'''
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new)); print("  ple-having-where re-patched")
# payment_entry: if() mysql -> CASE WHEN (postgres fix)
p = "/home/user/bench/apps/erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.py"
s = open(p).read()
pairs = [
    (
        '\t\t\tif({rounded_total_field}, {rounded_total_field}, {grand_total_field}) as invoice_amount,',
        '\t\t\tCASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END as invoice_amount,',
    ),
    (
        '\t\t\t(if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) - advance_paid) as outstanding_amount,',
        '\t\t\t(CASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END - advance_paid) as outstanding_amount,',
    ),
    (
        '\t\t\tand if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) > advance_paid',
        '\t\t\tand CASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END > advance_paid',
    ),
]
changed = False
for old, new in pairs:
    if old in s and new not in s:
        s = s.replace(old, new)
        changed = True
if changed:
    open(p, "w").write(s)
    print("  payment-if-case re-patched")
# payment_entry: double-quoted string literal -> single quotes (postgres fix)
old = '\t\t"{voucher_type}" as voucher_type, name as voucher_no, {account} as account,'
new = "\t\t'{voucher_type}' as voucher_type, name as voucher_no, {account} as account,"
if old in s and new not in s:
    s = s.replace(old, new)
    open(p, "w").write(s)
    print("  payment-quote re-patched")
# payment_entry: CASE WHEN numeric -> COALESCE(NULLIF(...)) (postgres fix)
pairs = [
    (
        'CASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END as invoice_amount,',
        'COALESCE(NULLIF({rounded_total_field}, 0), {grand_total_field}) as invoice_amount,',
    ),
    (
        '(CASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END - advance_paid) as outstanding_amount,',
        '(COALESCE(NULLIF({rounded_total_field}, 0), {grand_total_field}) - advance_paid) as outstanding_amount,',
    ),
    (
        'and CASE WHEN {rounded_total_field} THEN {rounded_total_field} ELSE {grand_total_field} END > advance_paid',
        'and COALESCE(NULLIF({rounded_total_field}, 0), {grand_total_field}) > advance_paid',
    ),
]
changed = False
for old, new in pairs:
    if old in s and new not in s:
        s = s.replace(old, new)
        changed = True
if changed:
    open(p, "w").write(s)
    print("  payment-nullif re-patched")
# payment_entry: status != "Closed" double-quote -> single quote (postgres fix)
old = '\t\t\tand status != "Closed"'
new = "\t\t\tand status != 'Closed'"
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new))
    print("  payment-closed-quote re-patched")
# payment_entry: PR.name in grouped subquery -> Max(PR.name) (postgres fix)
old = '''\t\t\tPR.outstanding_amount.as_("allocated_amount"),
\t\t\tPR.name.as_("payment_request"),
\t\t\tCount("*").as_("count"),'''
new = '''\t\t\tPR.outstanding_amount.as_("allocated_amount"),
\t\t\tMax(PR.name).as_("payment_request"),
\t\t\tCount("*").as_("count"),'''
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new))
    print("  payment-pr-max re-patched")
# payment_entry: import Max
old = "from frappe.query_builder.functions import Count"
new = "from frappe.query_builder.functions import Count, Max"
if old in s and new not in s:
    open(p, "w").write(s.replace(old, new))
    print("  payment-import-max re-patched")
PY

echo "===== [8/9] بوت‌استرپ دیتا ====="
rm -f /home/user/bench/sites/site1.local/locks/*.lock || true
if [ -f "$REPO/dev_bootstrap.py" ]; then
  cd /home/user/bench/sites
  /home/user/bench/env/bin/python "$REPO/dev_bootstrap.py"
fi
# مشتری‌های ثانویه قدیمی (اسنپ) هم به‌عنوان مشتری واقعی ساخته می‌شوند
cd /home/user/bench/sites
/home/user/bench/env/bin/python - <<'PYEOF'
import frappe
frappe.init(site="site1.local")
frappe.connect()
try:
    import restaurant.api as api
    so_rows = frappe.get_all(
        "Sales Order",
        fields=["restaurant_secondary_customer"],
        filters={"restaurant_secondary_customer": ["!=", ""]},
        ignore_permissions=True,
    )
    names = sorted({
        (r.get("restaurant_secondary_customer") or "").strip()
        for r in so_rows
        if (r.get("restaurant_secondary_customer") or "").strip()
    })
    for name in names:
        api._ensure_customer(name, "")
    if names:
        frappe.db.commit()
        print("  secondary customers ensured:", len(names))
except Exception:
    frappe.db.rollback()
    print("  secondary backfill skipped")
frappe.destroy()
PYEOF

echo "===== [9/9] نصب فرانت ====="
cd "$REPO/frontend"
[ -d node_modules ] || npm install

echo
echo "✅ REBUILD DONE — حالا سرویس‌ها را بالا بیاور:"
echo "   بک‌اند:  bench --site site1.local serve --port 8000 --noreload --nothreading"
echo "   فرانت:   cd frontend && npm run dev"
echo "   Admin:   Administrator / admin"
