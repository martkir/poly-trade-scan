"""Allow running as: python -m services.trade_monitor"""
from src.services.trade_monitor.run import main
import asyncio

asyncio.run(main())
