"""Compatibility shim for the Fastlit demo.

Prefer:
    fastlit run examples/app.py --dev
"""

from app import main


if __name__ == "__main__":
    main()
