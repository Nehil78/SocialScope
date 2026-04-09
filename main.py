from rich.console import Console
from rich.panel import Panel
import argparse
from pathlib import Path
import yaml
import csv
from datetime import datetime

console = Console()

def load_config():
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        console.print("[red]Config file nahi mila![/red]")
        exit(1)
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_deleted_to_csv(deleted_messages, output_dir="./output/deleted"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    file_path = Path(output_dir) / f"deleted_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Sender", "Message", "Status"])
        for msg in deleted_messages:
            writer.writerow([
                msg.get('readable_time', 'N/A'),
                msg.get('sender', 'Unknown'),
                msg.get('possible_text', msg.get('text', ''))[:300],
                msg.get('status', 'DELETED')
            ])
    console.print(f"[bold green]✅ Deleted messages saved → {file_path}[/bold green]")

def main():
    console.print(Panel.fit(
        "[bold red]SocialScope Forensic Toolkit[/bold red]\n"
        "[cyan]Instagram DM Forensic Tool - All Phases Ready[/cyan]",
        title="SSFT v1.0-alpha", border_style="red"
    ))

    parser = argparse.ArgumentParser(description="SocialScope Forensic Toolkit")
    parser.add_argument("--case", required=True, help="Case ID")
    parser.add_argument("--investigator", required=True, help="Investigator Name")
    parser.add_argument("--data-folder", required=True, help="Extracted data folder path")
    args = parser.parse_args()

    console.print(f"[green]Case:[/green] {args.case}")
    console.print(f"[green]Investigator:[/green] {args.investigator}")
    console.print(f"[green]Folder:[/green] {args.data_folder}")

    folder = Path(args.data_folder)
    if not (folder.exists() and folder.is_dir()):
        console.print("[red]Folder nahi mila![/red]")
        return

    config = load_config()

    # ====================== PHASE 1: Parsing ======================
    console.print("\n[bold cyan]═══ PHASE 1: Instagram Parsing ═══[/bold cyan]")
    from core.parser import InstagramParser
    insta_parser = InstagramParser(config, args.data_folder)
    messages = insta_parser.parse_direct_messages()

    if not messages:
        console.print("[yellow]No messages parsed[/yellow]")
        return

    console.print(f"[bold green]✓ {len(messages)} messages parsed[/bold green]")

    # ====================== PHASE 2: Master Timeline ======================
    console.print("\n[bold cyan]═══ PHASE 2: Master Timeline ═══[/bold cyan]")
    from core.timeline import MasterTimeline
    timeline = MasterTimeline(messages)
    timeline.build_timeline()
    timeline.preview_table(rows=15)
    timeline.save_to_csv()

    # ====================== PHASE 3: Deleted Recovery ======================
    console.print("\n[bold magenta]═══ PHASE 3: Deleted Message Recovery ═══[/bold magenta]")
    from core.wal_recovery import WALRecovery
    db_path = Path(args.data_folder) / "direct.db"
    deleted = []
    if db_path.exists():
        wal_rec = WALRecovery(db_path)
        deleted = wal_rec.recover_deleted()
        if deleted:
            console.print(f"[bold magenta]✓ {len(deleted)} deleted items recovered[/bold magenta]")
            save_deleted_to_csv(deleted)

    # ====================== PHASE 4: Keyword & Sentiment Alerting ======================
    console.print("\n[bold magenta]═══ PHASE 4: Keyword & Sentiment Alerting ═══[/bold magenta]")
    from core.keyword_alert import KeywordAlert
    alert_system = KeywordAlert(config)
    suspicious_messages = []

    for msg in messages:
        analysis = alert_system.analyze_message(msg.get('text', ''))
        msg['sentiment'] = analysis['status']
        msg['red_flags'] = analysis['flags']
        msg['is_suspicious'] = analysis['is_suspicious']

        if msg['is_suspicious']:
            suspicious_messages.append(msg)

    if suspicious_messages:
        console.print(f"[bold red]⚠️  {len(suspicious_messages)} Suspicious messages found![/bold red]")
        for msg in suspicious_messages[:8]:
            time = msg.get('readable_time', 'N/A')
            sender = msg.get('sender', 'Unknown')
            text = msg.get('text', '')[:100]
            flags = ", ".join(msg['red_flags']) if msg['red_flags'] else "None"
            console.print(f"  • {time} | {sender} → {text} | Flags: {flags} | {msg['sentiment']}")
    else:
        console.print("[green]No red flag messages found.[/green]")

    # ====================== PHASE 5: Hash + Media + EXIF ======================
    console.print("\n[bold magenta]═══ PHASE 5: Hash Integrity + Media & EXIF ═══[/bold magenta]")
    from core.media_extractor import MediaExtractor
    extractor = MediaExtractor(args.data_folder)
    db_hash = extractor.calculate_sha256(db_path)
    console.print(f"[bold green]Direct.db SHA-256 Hash:[/bold green] {db_hash}")
    extractor.extract_media_from_db(messages)

    # ====================== PHASE 6: Network Graph ======================
    console.print("\n[bold magenta]═══ PHASE 6: Network Link Analysis ═══[/bold magenta]")
    from core.network_graph import NetworkGraph
    graph = NetworkGraph(messages)
    graph.build_graph()
    graph.show_top_contacts(top=6)
    graph.save_interactive_graph()

    # ====================== PHASE 7: Final Report ======================
    console.print("\n[bold magenta]═══ PHASE 7: Professional Forensic Report ═══[/bold magenta]")
    from core.report_generator import ForensicReport
    report = ForensicReport(args.case, args.investigator)
    report.generate_report(messages, deleted, suspicious_messages, db_hash)

    console.print("\n[bold green]=== ALL PHASES COMPLETED SUCCESSFULLY ===[/bold green]")

if __name__ == "__main__":
    main()