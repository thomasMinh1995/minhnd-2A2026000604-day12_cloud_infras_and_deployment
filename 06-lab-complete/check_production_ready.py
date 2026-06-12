"""
Production Readiness Checker

Tự động kiểm tra project có đủ điều kiện deploy chưa.
Chạy: python check_production_ready.py
"""
import os
import sys


def check(name: str, passed: bool, detail: str = "") -> dict:
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))
    return {"name": name, "passed": passed}


def _read_files(base: str, paths: list[str]) -> str:
    content = ""
    for path in paths:
        fpath = os.path.join(base, path)
        if os.path.exists(fpath):
            content += open(fpath).read() + "\n"
    return content


def run_checks():
    results = []
    base = os.path.dirname(__file__)
    app_files = [
        "app/main.py",
        "app/config.py",
        "app/auth.py",
        "app/rate_limiter.py",
        "app/cost_guard.py",
        "app/redis_client.py",
        "app/agent.py",
        "app/logging_config.py",
        "app/schemas.py",
    ]

    print("\n" + "=" * 55)
    print("  Production Readiness Check — Day 12 Lab")
    print("=" * 55)

    print("\n📁 Required Files")
    results.append(check("Dockerfile exists", os.path.exists(os.path.join(base, "Dockerfile"))))
    results.append(check(
        "docker-compose.yml exists",
        os.path.exists(os.path.join(base, "docker-compose.yml")),
    ))
    results.append(check(
        ".dockerignore exists",
        os.path.exists(os.path.join(base, ".dockerignore")),
    ))
    results.append(check(
        ".env.example exists",
        os.path.exists(os.path.join(base, ".env.example")),
    ))
    results.append(check(
        "requirements.txt exists",
        os.path.exists(os.path.join(base, "requirements.txt")),
    ))
    results.append(check(
        "nginx config exists",
        os.path.exists(os.path.join(base, "nginx", "nginx.conf")),
    ))
    results.append(check(
        "railway.toml or render.yaml exists",
        os.path.exists(os.path.join(base, "railway.toml"))
        or os.path.exists(os.path.join(base, "render.yaml")),
    ))
    results.append(check(
        "CI workflow exists",
        os.path.exists(os.path.join(base, "..", ".github", "workflows", "lab6-ci.yml")),
    ))
    for module in app_files:
        results.append(check(
            f"{module} exists",
            os.path.exists(os.path.join(base, module)),
        ))

    print("\n🔒 Security")
    env_ignored = False
    for gi in [os.path.join(base, ".gitignore"), os.path.join(base, "..", ".gitignore")]:
        if os.path.exists(gi) and ".env" in open(gi).read():
            env_ignored = True
            break
    results.append(check(".env in .gitignore", env_ignored))

    secrets_found = []
    for path in app_files:
        fpath = os.path.join(base, path)
        if os.path.exists(fpath):
            content = open(fpath).read()
            for bad in ["sk-", "password123", "hardcoded"]:
                if bad in content:
                    secrets_found.append(f"{path}:{bad}")
    results.append(check(
        "No hardcoded secrets in code",
        len(secrets_found) == 0,
        str(secrets_found) if secrets_found else "",
    ))

    print("\n🌐 API Endpoints (code check)")
    code = _read_files(base, app_files)
    results.append(check("/health endpoint defined", '"/health"' in code or "'/health'" in code))
    results.append(check("/ready endpoint defined", '"/ready"' in code or "'/ready'" in code))
    results.append(check("POST /ask endpoint defined", '"/ask"' in code or "'/ask'" in code))
    results.append(check("Authentication implemented", "verify_api_key" in code or "api_key" in code.lower()))
    results.append(check("Rate limiting implemented", "rate:" in code or "rate_limit" in code.lower()))
    results.append(check("Cost guard implemented", "cost:" in code or "cost_guard" in code.lower()))
    results.append(check("Redis conversation storage", "conversation:" in code))
    results.append(check("Graceful shutdown (SIGTERM)", "SIGTERM" in code))
    results.append(check("Structured logging (JSON)", "json.dumps" in code or '"event"' in code))

    print("\n🐳 Docker")
    dockerfile = os.path.join(base, "Dockerfile")
    if os.path.exists(dockerfile):
        content = open(dockerfile).read()
        results.append(check("Multi-stage build", "AS builder" in content or "AS runtime" in content))
        results.append(check("Non-root user", "useradd" in content or "USER " in content))
        results.append(check("HEALTHCHECK instruction", "HEALTHCHECK" in content))
        results.append(check("Slim base image", "slim" in content or "alpine" in content))

    compose = os.path.join(base, "docker-compose.yml")
    if os.path.exists(compose):
        content = open(compose).read()
        results.append(check("Compose includes redis", "redis:" in content))
        results.append(check("Compose includes nginx", "nginx:" in content))

    dockerignore = os.path.join(base, ".dockerignore")
    if os.path.exists(dockerignore):
        content = open(dockerignore).read()
        results.append(check(".dockerignore covers .env", ".env" in content))
        results.append(check(".dockerignore covers __pycache__", "__pycache__" in content))

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    pct = round(passed / total * 100)

    print("\n" + "=" * 55)
    print(f"  Result: {passed}/{total} checks passed ({pct}%)")
    if pct == 100:
        print("  🎉 PRODUCTION READY! Deploy nào!")
    elif pct >= 80:
        print("  ✅ Almost there! Fix the ❌ items above.")
    else:
        print("  ❌ Not ready. Review the checklist carefully.")
    print("=" * 55 + "\n")
    return pct == 100


if __name__ == "__main__":
    ready = run_checks()
    sys.exit(0 if ready else 1)
