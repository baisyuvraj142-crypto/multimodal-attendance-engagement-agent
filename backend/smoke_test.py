import sys
import importlib

def run_smoke_test():
    print("=" * 60)
    print(" EduSense AI - System Smoke Test")
    print("=" * 60)
    
    required_libraries = [
        "fastapi",
        "uvicorn",
        "cv2",
        "numpy",
        "pandas",
        "sqlalchemy",
        "reportlab",
        "dotenv",
    ]

    all_passed = True
    for lib in required_libraries:
        try:
            mod = importlib.import_module(lib)
            version = getattr(mod, "__version__", "installed")
            print(f" [PASS] {lib:15s} (v{version})")
        except Exception as e:
            print(f" [FAIL] {lib:15s} ({e})")
            all_passed = False

    # Check local core modules
    print("\nChecking Core Modules:")
    core_modules = [
        "core.config",
        "core.database",
        "core.face_detection",
        "core.tracking",
        "core.camera_service",
        "core.audio_analysis",
        "core.fusion",
        "core.engagement",
        "core.recommendations_engine",
        "core.ai_suggestions",
        "core.llm_insights",
        "core.analytics_service",
        "core.teacher_profiles",
        "main"
    ]

    for mod_name in core_modules:
        try:
            importlib.import_module(mod_name)
            print(f" [PASS] {mod_name}")
        except Exception as e:
            print(f" [FAIL] {mod_name}: {e}")
            all_passed = False

    print("=" * 60)
    if all_passed:
        print(" ALL SMOKE TESTS PASSED! Backend is ready to launch.")
        return 0
    else:
        print(" SOME MODULES FAILED SMOKE TEST.")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())
