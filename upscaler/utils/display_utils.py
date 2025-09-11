"""
Rich-based display utilities for beautiful terminal UI - Improved version.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import humanize

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    # Force UTF-8 encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Rich imports
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress, 
    BarColumn, 
    TextColumn, 
    TimeRemainingColumn,
    TimeElapsedColumn,
    SpinnerColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    ProgressColumn,
    DownloadColumn,
    TransferSpeedColumn
)
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
from rich.style import Style
from rich.columns import Columns
from rich.live import Live

# Initialize Rich console with optimized settings for Windows
# Check if running in Windows Terminal (WT_SESSION env var)
is_windows_terminal = os.environ.get('WT_SESSION') is not None

console = Console(
    # Use legacy mode only for old Windows console, not Windows Terminal
    legacy_windows=False if is_windows_terminal else (True if sys.platform == 'win32' else None),
    force_terminal=True,  # Force terminal mode for better control
    soft_wrap=False  # Disable soft wrap for more stable rendering
)

def set_windows_terminal_progress(percent: float, state: int = 1):
    """
    Set Windows Terminal tab/taskbar progress indicator using OSC 9;4 sequence.
    
    Args:
        percent: Progress percentage (0-100)
        state: 0=hide, 1=normal, 2=error, 3=indeterminate, 4=warning
    
    This only works in Windows Terminal, not in legacy console.
    """
    if is_windows_terminal:
        # Clamp percentage to 0-100
        percent = max(0, min(100, int(percent)))
        # Send OSC 9;4 sequence
        sys.stdout.write(f"\x1b]9;4;{state};{percent}\x07")
        sys.stdout.flush()

# Color scheme
COLORS = {
    'primary': 'bright_cyan',
    'secondary': 'cyan',
    'success': 'bright_green',
    'warning': 'yellow',
    'error': 'bright_red',
    'info': 'bright_blue',
    'accent': 'magenta',
    'dim': 'grey50',
    'highlight': 'bold bright_white'
}

class SpeedColumn(ProgressColumn):
    """Custom column to show processing speed with fixed width."""
    
    def __init__(self):
        # Fixed width to prevent layout shifts
        from rich.table import Column
        super().__init__(table_column=Column(width=10, no_wrap=True, justify="right"))
    
    def render(self, task):
        """Render the speed."""
        speed = task.fields.get('speed', 0.0)
        # Fixed width format to prevent flickering
        return Text(f"{speed:5.1f} fps", style="bright_yellow")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    return humanize.naturalsize(size_bytes, binary=True)

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed file information."""
    path = Path(file_path)
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        'name': path.name,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': path.suffix.lower()
    }

def create_header_panel(title: str, subtitle: Optional[str] = None) -> Panel:
    """Create a beautiful header panel."""
    header_text = Text(title, style=f"bold {COLORS['highlight']}")
    header_text = Align.center(header_text)
    
    return Panel(
        header_text,
        box=box.DOUBLE,
        style=f"{COLORS['primary']}",
        subtitle=subtitle,
        subtitle_align="center",
        padding=(0, 1)
    )

def create_info_table(data: List[tuple], title: str = "", compact: bool = False) -> Table:
    """Create a nicely formatted info table."""
    table = Table(
        show_header=False,
        box=None if compact else box.SIMPLE,
        padding=(0, 1),
        expand=True,
        pad_edge=True,  # Pad to edge of terminal
        show_edge=False
    )
    
    # Fixed widths to prevent misalignment with emojis
    label_width = 20 if compact else 25
    table.add_column("Label", style=COLORS['secondary'], width=label_width, no_wrap=True)
    table.add_column("Value", style=COLORS['highlight'], overflow="fold")
    
    for label, value in data:
        table.add_row(label, str(value))
    
    return table

def create_two_column_panel(left_data: List[tuple], right_data: List[tuple], 
                           left_title: str, right_title: str) -> Panel:
    """Create a panel with two columns of information."""
    # Helper function to extract emoji from label
    def extract_emoji_and_text(label: str) -> tuple:
        """Extract emoji and text from a label string."""
        label = label.strip()
        # Check for common emojis at start
        if label and len(label) >= 2:
            # Try to detect emoji (very simplified - checks if first chars are non-ASCII)
            if ord(label[0]) > 127:  
                # Find where emoji ends (usually 1-2 chars, sometimes more with modifiers)
                emoji_end = 1
                while emoji_end < min(4, len(label)) and ord(label[emoji_end]) > 127:
                    emoji_end += 1
                return label[:emoji_end], label[emoji_end:].strip()
        return "", label
    
    # Create a single table with 4 columns for better alignment
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),  # Padding between columns
        expand=True,
        pad_edge=False,
        show_edge=False
    )
    
    # Add columns - combine emoji with label
    table.add_column("L1", style=COLORS['info'], width=18, no_wrap=True)  # Left label with emoji
    table.add_column("V1", style=COLORS['highlight'], width=22)  # Left value
    table.add_column("L2", style=COLORS['accent'], width=18, no_wrap=True)  # Right label with emoji
    table.add_column("V2", style=COLORS['highlight'], width=22)  # Right value
    
    # Add section headers
    table.add_row(
        f"[bold {COLORS['info']}]── {left_title} ──[/bold {COLORS['info']}]", "",
        f"[bold {COLORS['accent']}]── {right_title} ──[/bold {COLORS['accent']}]", ""
    )
    
    # Add data rows
    max_rows = max(len(left_data), len(right_data))
    for i in range(max_rows):
        # Process left side
        if i < len(left_data):
            left_label = left_data[i][0]
            left_value = str(left_data[i][1])
        else:
            left_label, left_value = "", ""
            
        # Process right side
        if i < len(right_data):
            right_label = right_data[i][0]
            right_value = str(right_data[i][1]) 
        else:
            right_label, right_value = "", ""
        
        table.add_row(left_label, left_value, right_label, right_value)
    
    return Panel(
        table,
        box=box.ROUNDED,
        border_style=COLORS['primary'],
        padding=(0, 1)
    )

def display_zetta_logo():
    """Display ZETTA MEDIA ASCII art with gradient."""
    # 3D Slant style ASCII art for ZETTA MEDIA
    logo_3d = [
        r"   _____________________  ___       __  ________________  _____   ",
        r"  /__  / ____/_  __/_  __/   |     /  |/  / ____/ __ \_ |/   |  ",
        r"    / / __/   / /   / / / /| |    / /|_/ / __/ / / / // // /| |  ",
        r"   / / /___  / /   / / / ___ |   / /  / / /___/ /_/ // // ___ |  ",
        r"  /_/_____/ /_/   /_/ /_/  |_|  /_/  /_/_____/_____/___/_/  |_|  "
    ]
    
    # Alternative: ANSI Shadow style with depth
    logo_shadow = [
        "███████╗███████╗████████╗████████╗ █████╗     ███╗   ███╗███████╗██████╗ ██╗ █████╗ ",
        "╚══███╔╝██╔════╝╚══██╔══╝╚══██╔══╝██╔══██╗    ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗",
        "  ███╔╝ █████╗     ██║      ██║   ███████║    ██╔████╔██║█████╗  ██║  ██║██║███████║",
        " ███╔╝  ██╔══╝     ██║      ██║   ██╔══██║    ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║",
        "███████╗███████╗   ██║      ██║   ██║  ██║    ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║",
        "╚══════╝╚══════╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝    ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝"
    ]
    
    # Modern isometric 3D style
    logo_iso = [
        "╔══╗╔══╗╔══╗╔══╗╔══╗    ╔╗╔╗╔══╗╔══╗╔══╗╔══╗",
        "╚╗─║║╔═╝╚╗─║╚╗─║║╔╗║    ║╚╝║║╔═╝║╔╗║╚╗╔╝║╔╗║",
        " ║─║║╚═╗ ║─║ ║─║║╚╝║    ║║║║║╚═╗║║║║ ║║ ║╚╝║",
        "╔╝─║║╔═╝ ║─║ ║─║║╔╗║    ║║║║║╔═╝║║║║ ║║ ║╔╗║",
        "╚══╝╚══╝ ╚═╝ ╚═╝╚╝╚╝    ╚╩╩╝╚══╝╚══╝ ╚╝ ╚╝╚╝"
    ]
    
    from rich.text import Text
    from rich.align import Align
    
    # Let's use the shadow style with soft blue gradient
    for i, line in enumerate(logo_shadow):
        styled_text = Text()
        
        # Create smooth gradient effect with soft blue tones
        for j, char in enumerate(line):
            # Calculate position for gradient (0.0 to 1.0)
            pos = j / max(1, len(line) - 1)
            
            if char not in [' ', '╚', '╔', '╝', '╗', '═', '║']:
                # Main blocks - soft blue gradient
                if pos < 0.1:
                    color = "#E6F3FF"  # Very light blue
                elif pos < 0.25:
                    color = "#B3D9FF"  # Light blue
                elif pos < 0.4:
                    color = "#80BFFF"  # Light-medium blue
                elif pos < 0.55:
                    color = "#4DA6FF"  # Medium blue
                elif pos < 0.7:
                    color = "#1A8CFF"  # Medium-dark blue
                elif pos < 0.85:
                    color = "#0066CC"  # Dark blue
                else:
                    color = "#004C99"  # Very dark blue
                styled_text.append(char, style=f"bold {color}")
            elif char in ['╚', '╔', '╝', '╗', '═', '║']:
                # Shadow/border elements - subtle grey-blue
                if pos < 0.5:
                    styled_text.append(char, style="#99B3CC")
                else:
                    styled_text.append(char, style="#668099")
            else:
                styled_text.append(char)
        
        console.print(Align.center(styled_text))
    
    # Add a subtle professional tagline
    tagline_text = "━━━  AI-POWERED VIDEO ENHANCEMENT  ━━━"
    tagline = Text()
    
    # Soft blue gradient for tagline to match logo
    for i, char in enumerate(tagline_text):
        pos = i / max(1, len(tagline_text) - 1)
        if char == '━':
            tagline.append(char, style="#668099")  # Subtle grey-blue
        elif char != ' ':
            # Soft blue gradient for text
            if pos < 0.5:
                tagline.append(char, style="italic #4DA6FF")  # Medium blue
            else:
                tagline.append(char, style="italic #1A8CFF")  # Medium-dark blue
        else:
            tagline.append(char)
    
    console.print(Align.center(tagline))
    console.print("")  # Empty line after logo

def display_processing_start(input_path: str, output_path: str, mode: str, **kwargs):
    """Display beautiful processing start information."""
    # Clear console more thoroughly for Windows
    if sys.platform == 'win32':
        # Clear screen and move cursor to home
        os.system('cls')
        # Alternative method using ANSI escape codes
        print('\033[2J\033[H', end='')
    else:
        console.clear()
    
    # Reset console and ensure clean display
    console.print("\033[0m")  # Reset all attributes
    console.print("")  # Single blank line
    
    # Display ZETTA MEDIA logo
    display_zetta_logo()
    
    # Determine mode icon and title
    mode_icon = "🎬" if mode == "VIDEO" else "🖼️"
    title = f"{mode_icon} {mode} UPSCALING STARTED"
    
    # Create header
    header = create_header_panel(title)
    console.print(header)
    console.print("")
    
    # Get file info
    file_info = get_file_info(input_path)
    
    # Prepare file data
    if file_info:
        file_data = [
            ("📁 File", file_info['name']),
            ("💾 Size", file_info['size_formatted']),
            ("📅 Modified", file_info['modified']),
        ]
    else:
        file_data = [
            ("📁 File", Path(input_path).name),
            ("📂 Path", str(input_path)),
        ]
    
    # Processing settings
    settings_data = [
        ("🤖 Model", kwargs.get('model', 'realesr-general-x4v3')),
        ("📏 Scale", f"{kwargs.get('scale', 4)}x"),
        ("🧩 Tile", f"{kwargs.get('tile', 0)}px" if kwargs.get('tile', 0) > 0 else "Auto"),
        ("⚡ Backend", kwargs.get('backend', 'auto')),
    ]
    
    if kwargs.get('face_enhance', False):
        settings_data.append(("😊 Face", f"Enhanced ({kwargs.get('face_strength', 1.0)})"))
    
    # Create two-column layout
    info_panel = create_two_column_panel(
        file_data, settings_data,
        "Input File", "Settings"
    )
    console.print(info_panel)
    
    # Output info panel
    output_data = [
        ("📂 Output", Path(output_path).name),
        ("🎯 Format", Path(output_path).suffix.upper()[1:] or "Unknown"),
    ]
    
    output_panel = Panel(
        create_info_table(output_data, compact=True),
        title=f"[bold {COLORS['success']}]Output Configuration[/bold {COLORS['success']}]",
        box=box.ROUNDED,
        border_style=COLORS['success'],
        padding=(0, 2)
    )
    console.print(output_panel)
    console.print("")

def make_video_info_panel(video_info: Dict[str, Any], label: str = "Input Video Information", file_path: Optional[str] = None) -> Panel:
    """Build (not print) a video info panel renderable."""
    # Build data list with emojis separated
    video_data = []
    
    # File name (if provided)
    if file_path:
        video_data.append(("📁", "File Name", Path(file_path).name))
    
    # Resolution
    video_data.append(("🎥", "Resolution", f"{video_info['width']} × {video_info['height']}"))
    
    # Frame Rate  
    video_data.append(("🎞", "Frame Rate", f"{video_info['fps']:.2f} fps"))  # Removed modifier
    
    # Total Frames
    if video_info.get('total_frames'):
        frames_value = f"{video_info['total_frames']:,}"
    else:
        frames_value = "N/A"
    video_data.append(("📊", "Total Frames", frames_value))
    
    # Duration
    if video_info.get('duration'):
        duration_sec = video_info['duration']
        hours = int(duration_sec // 3600)
        minutes = int((duration_sec % 3600) // 60)
        seconds = int(duration_sec % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        video_data.append(("⏱", "Duration", duration_str))  # Removed modifier
    
    # Codec
    if video_info.get('codec'):
        video_data.append(("🎬", "Codec", video_info['codec']))
    
    # Bitrate
    if video_info.get('bitrate'):
        bitrate_mbps = video_info['bitrate'] / 1_000_000
        video_data.append(("📶", "Bitrate", f"{bitrate_mbps:.2f} Mbps"))
    
    # Create table with 2 columns (emoji+label, value)
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 1),  # Small padding between columns
        expand=True,
        show_edge=False,
        pad_edge=False  # Don't pad to edge
    )
    
    # Two columns: emoji+label combined, value separate
    table.add_column("", width=18, style=COLORS['info'], no_wrap=True)  # Combined emoji+label
    table.add_column("", style=COLORS['highlight'])  # Value column
    
    # Add rows with emoji and label combined
    for emoji, label_text, value in video_data:
        # Add extra space for narrow emojis to align with others
        if emoji in ["🎞", "⏱"]:
            table.add_row(f"{emoji}  {label_text}", value)  # Double space
        else:
            table.add_row(f"{emoji} {label_text}", value)  # Single space
    
    # Create panel
    panel = Panel(
        table,
        title=f"[bold {COLORS['info']}]{label}[/bold {COLORS['info']}]",
        box=box.ROUNDED,
        border_style=COLORS['info'],
        padding=(0, 1),  # Reduced padding for tighter layout
        expand=True
    )
    
    return panel


def display_video_info(video_info: Dict[str, Any], label: str = "Video Information", file_path: Optional[str] = None):
    """Legacy: print the video info panel to console."""
    panel = make_video_info_panel(video_info, label, file_path)
    console.print(panel)
    console.print("")

def display_processing_complete(input_path: str, output_path: str, mode: str, 
                               start_time: float, end_time: float, **kwargs):
    """Display beautiful processing completion information."""
    # Calculate elapsed time
    elapsed = end_time - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Get file info
    input_info = get_file_info(input_path)
    output_info = get_file_info(output_path)
    
    # Create completion panel
    mode_icon = "🎬" if mode == "VIDEO" else "🖼️"
    
    completion_text = f"✨ {mode} UPSCALING COMPLETED! ✨"
    header_panel = create_header_panel(
        completion_text,
        f"Processed in {time_str}"
    )
    
    console.print("")
    console.print(header_panel)
    console.print("")
    
    # File comparison and summary in two columns
    if input_info and output_info:
        comparison_data = [
            ("📥 Original", input_info['size_formatted']),
            ("📤 Output", output_info['size_formatted']),
            ("📈 Ratio", f"{output_info['size'] / input_info['size']:.2f}x"),
        ]
    else:
        comparison_data = [
            ("📥 Input", Path(input_path).name),
            ("📤 Output", Path(output_path).name),
        ]
    
    summary_data = [
        ("🤖 Model", kwargs.get('model', 'realesr-general-x4v3')),
        ("📏 Scale", f"{kwargs.get('scale', 4)}x"),
        ("⚙  Backend", kwargs.get('backend_used', 'Unknown')),  # Removed modifier, added space
    ]
    
    results_panel = create_two_column_panel(
        comparison_data, summary_data,
        "File Comparison", "Processing Summary"
    )
    console.print(results_panel)
    
    # Output location with nice formatting
    output_panel = Panel(
        Align.center(
            Text(output_path, style=f"bold {COLORS['success']}")
        ),
        title="[bold bright_green]📁 OUTPUT FILE SAVED[/bold bright_green]",
        box=box.DOUBLE,
        border_style=COLORS['success'],
        padding=(0, 2)
    )
    console.print(output_panel)
    
    # Success message
    success_text = Text(
        f"🎉 Your {mode.lower()} has been successfully upscaled! 🎉",
        style=f"bold {COLORS['success']}",
        justify="center"
    )
    console.print("")
    console.print(success_text)
    console.print("")

def display_backend_info(backend_name: str, backend_info: Dict[str, Any]):
    """Display backend information."""
    backend_data = [
        ("🔌 Backend", backend_name),
    ]
    
    if backend_info.get('device'):
        device_icon = "🎮" if "cuda" in str(backend_info['device']).lower() else "💻"
        backend_data.append((f"{device_icon} Device", backend_info['device']))
    
    if backend_info.get('gpu_name'):
        backend_data.append(("🎮 GPU", backend_info['gpu_name']))
    
    if backend_info.get('cuda_available') is not None:
        cuda_status = "✅ Available" if backend_info['cuda_available'] else "❌ Not Available"
        backend_data.append(("🚀 CUDA", cuda_status))
    
    panel = Panel(
        create_info_table(backend_data, compact=True),
        title=f"[bold {COLORS['primary']}]Backend Information[/bold {COLORS['primary']}]",
        box=box.ROUNDED,
        border_style=COLORS['primary'],
        padding=(0, 2)
    )
    
    console.print(panel)

def create_progress() -> Progress:
    """Create a beautiful progress bar with minimal flickering."""
    # Decide whether to include spinner based on platform
    columns = []
    
    # Skip spinner on Windows to reduce flicker (optional - comment out if you want spinner)
    if sys.platform != 'win32':
        columns.append(SpinnerColumn(style=COLORS['primary'], speed=1.2))
    
    columns.extend([
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(
            style=COLORS['primary'],
            complete_style=COLORS['success'],
            finished_style=COLORS['success'],
            bar_width=40  # Fixed width to prevent layout shifts
        ),
        TaskProgressColumn(),
        TextColumn("•"),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        SpeedColumn(),  # Now with fixed width
    ])
    
    return Progress(
        *columns,
        console=console,
        expand=False,  # Don't expand - prevents width fluctuations
        transient=True,  # Update in-place to reduce flicker
        auto_refresh=False,  # KEY: Manual refresh control only!
        redirect_stdout=False,  # Don't redirect stdout
        redirect_stderr=False   # Don't redirect stderr
    )

# Convenience functions for backward compatibility
def print_info(label: str, value: str, indent: int = 2):
    """Print labeled information (for compatibility)."""
    console.print(f"{' ' * indent}[{COLORS['secondary']}]{label}[/{COLORS['secondary']}]: [{COLORS['highlight']}]{value}[/{COLORS['highlight']}]")

def print_success(message: str):
    """Print success message."""
    console.print(f"[{COLORS['success']}]✅ {message}[/{COLORS['success']}]")

def print_warning(message: str):
    """Print warning message."""
    console.print(f"[{COLORS['warning']}]⚠️  {message}[/{COLORS['warning']}]")

def print_error(message: str):
    """Print error message."""
    console.print(f"[{COLORS['error']}]❌ {message}[/{COLORS['error']}]")

def print_separator(char='─', length=80):
    """Print a separator line."""
    console.print(f"[{COLORS['dim']}]{char * length}[/{COLORS['dim']}]")

def print_header(title: str):
    """Print a styled header."""
    console.print("")
    console.print(Panel(
        Align.center(Text(title.upper(), style=f"bold {COLORS['highlight']}")),
        box=box.DOUBLE,
        style=COLORS['primary']
    ))
    console.print("")