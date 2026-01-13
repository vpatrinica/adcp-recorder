import logging
import sys
from pathlib import Path

import click

from adcp_recorder.config import RecorderConfig
from adcp_recorder.core.recorder import AdcpRecorder
from adcp_recorder.serial.port_manager import list_serial_ports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@click.group()
def cli():
    """ADCP Recorder Control Plane"""
    pass


@cli.command()
def list_ports():
    """List available serial ports."""
    ports = list_serial_ports()
    if not ports:
        click.echo("No serial ports found.")
        return

    click.echo(f"Found {len(ports)} ports:")
    for port in ports:
        click.echo(f"  {port.device}: {port.description} ({port.hwid})")


@cli.command()
@click.option("--port", help="Serial port device (e.g. /dev/ttyUSB0)")
@click.option("--baud", type=int, help="Baud rate")
@click.option("--output", help="Output directory")
@click.option("--debug/--no-debug", default=None, help="Enable debug logging")
def configure(port, baud, output, debug):
    """Update configuration settings."""
    config = RecorderConfig.load()

    updates = {}
    if port:
        updates["serial_port"] = port
    if baud:
        updates["baudrate"] = baud
    if output:
        updates["output_dir"] = output
    if debug is not None:
        updates["log_level"] = "DEBUG" if debug else "INFO"

    if updates:
        config.update(**updates)
        click.echo(f"Configuration updated in {config.get_config_path()}")
        # Show current config
        click.echo(f"  Port: {config.serial_port}")
        click.echo(f"  Baud: {config.baudrate}")
        click.echo(f"  Output: {config.output_dir}")
        click.echo(f"  Level: {config.log_level}")
    else:
        click.echo("No changes specified.")
        click.echo(f"Current configuration ({config.get_config_path()}):")
        click.echo(f"  Port: {config.serial_port}")
        click.echo(f"  Baud: {config.baudrate}")
        click.echo(f"  Output: {config.output_dir}")
        click.echo(f"  Level: {config.log_level}")


@cli.command()
def start():
    """Start the recorder with current configuration."""
    config = RecorderConfig.load()

    # Update logging level based on config
    logging.getLogger().setLevel(config.log_level)

    recorder = AdcpRecorder(config)
    click.echo(f"Starting recorder on {config.serial_port} at {config.baudrate} baud...")
    click.echo(f"Data will be saved to {config.output_dir}")
    click.echo("Press Ctrl+C to stop.")

    recorder.run_blocking()


@cli.command()
def status():
    """Show current configuration and status."""
    config = RecorderConfig.load()

    click.echo("ADCP Recorder Status")
    click.echo("====================")
    click.echo(f"Configuration File: {config.get_config_path()}")
    click.echo(f"Serial Port:       {config.serial_port}")
    click.echo(f"Baud Rate:         {config.baudrate}")
    click.echo(f"Output Directory:  {config.output_dir}")
    click.echo(f"Log Level:         {config.log_level}")

    # Simple validation
    click.echo("\nSystem Checks:")

    # Check output dir
    out_path = Path(config.output_dir)
    if out_path.exists():
        click.echo("  [OK] Output directory exists")
    else:
        click.echo("  [WARNING] Output directory does not exist (will be created on start)")

    # Check port (simple existence check if possible without opening)
    from adcp_recorder.serial.port_manager import list_serial_ports

    ports = [p.device for p in list_serial_ports()]
    if config.serial_port in ports:
        click.echo(f"  [OK] Serial port {config.serial_port} found")
    else:
        click.echo(f"  [WARNING] Serial port {config.serial_port} not found in available ports")


@cli.command()
@click.option(
    "--platform",
    type=click.Choice(["linux", "windows"]),
    required=True,
    help="Target platform",
)
@click.option("--out", type=click.Path(), default=".", help="Output directory for template")
def generate_service(platform, out):
    """Generate OS service configuration templates."""
    import shutil

    import adcp_recorder.templates

    # We need to find the package path.
    base_path = Path(adcp_recorder.templates.__file__).parent

    if platform == "linux":
        src = base_path / "linux" / "adcp-recorder.service"
        dst_name = "adcp-recorder.service"
    elif platform == "windows":
        # Instead of a template file, we generate a README or script that calls the python module
        dst_name = "install_service.bat"
        # We'll write content directly since it's simple
        content = (
            "@echo off\n"
            "REM Install ADCP Recorder Service\n"
            "REM Ensure python is in PATH and pywin32 is installed\n"
            "python -m adcp_recorder.service.win_service install\n"
            "python -m adcp_recorder.service.win_service start\n"
            "echo Service installed and started.\n"
            "pause\n"
        )

        dst = Path(out) / dst_name
        try:
            with open(dst, "w") as f:
                f.write(content)
            click.echo(f"Generated {dst_name} in {out}")
            click.echo("Run this script as Administrator to install the service.")
            return  # Skip copy fallback
        except Exception as e:
            click.echo(f"Error generating script: {e}")
            return

    dst = Path(out) / dst_name

    try:
        shutil.copy(src, dst)
        click.echo(f"Generated {dst_name} in {out}")
        click.echo("Please edit the file to match your system paths/user.")
    except Exception as e:
        click.echo(f"Error generating template: {e}")


if __name__ == "__main__":
    cli()
