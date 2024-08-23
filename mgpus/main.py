import click
import psutil
import pynvml
from rich import box
from rich.console import Console
from rich.table import Table


@click.command()
def cli():
    # Initialize NVML
    pynvml.nvmlInit()

    # Get the number of GPUs
    device_count = pynvml.nvmlDeviceGetCount()

    gpu_data = {f"GPU {i}": [] for i in range(device_count)}
    gpu_total_memory = {f"GPU {i}": pynvml.nvmlDeviceGetMemoryInfo(pynvml.nvmlDeviceGetHandleByIndex(i)).total / 1024 / 1024 / 1024 for i in range(device_count)}
    gpu_memory_used = {f"GPU {i}": 0 for i in range(device_count)}

    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)

        # Get processes running on the GPU
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)

        for process in processes:
            try:
                process_info = psutil.Process(process.pid)
                process_name = process_info.cmdline()
                process_name = ' '.join(process_name) if process_name else "Unknown"
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                process_name = "Unknown"
            
            memory_usage_gb = process.usedGpuMemory / 1024 / 1024 / 1024
            gpu_memory_used[f"GPU {i}"] += memory_usage_gb
            gpu_data[f"GPU {i}"].append(f"{process_name} (PID {process.pid}), {memory_usage_gb:.2f} GB")

    print_gpu_processes_table(gpu_data, gpu_total_memory, gpu_memory_used)
    return gpu_data, gpu_total_memory, gpu_memory_used


def print_gpu_processes_table(gpu_data, gpu_total_memory, gpu_memory_used) -> None:
    console = Console()
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("GPU", style="cyan")
    table.add_column("Memory Usage (Used/Total)", style="green")
    table.add_column("Processes", style="yellow")

    for gpu, processes in gpu_data.items():
        memory_usage = f"{gpu_memory_used[gpu]:.2f} / {gpu_total_memory[gpu]:.2f} GB"
        table.add_row(gpu, memory_usage, "")
        for process in processes:
            table.add_row("", "", process)

    console.print(table)


if __name__ == "__main__":
    cli()