"""
Main entry point for the upscaler package.
Allows running as: python -m upscaler
"""

from .cli import cli

if __name__ == '__main__':
    cli()