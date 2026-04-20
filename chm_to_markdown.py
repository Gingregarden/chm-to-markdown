import os
import subprocess
import shutil
import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

class SimpleHTMLToMD(HTMLParser):
    def __init__(self, section_name):
        super().__init__()
        self.section_name = section_name
        self.result = [f"# Section: {section_name}\n\n"]
        self.stack = []
        self.in_code = False
        self.in_table = False
        self.current_table = []
        self.current_row = []
        self.skip_content = False
        self.code_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "").lower()
        
        if tag in ["script", "style", "meta", "link", "title"]:
            self.skip_content = True
            return

        if tag in ["h1", "h2", "h3"]:
            level = int(tag[1])
            self.result.append("\n" + "#" * level + " ")
        
        elif tag == "a":
            self.result.append("**")
        
        elif tag == "pre" or (tag == "div" and any(c in classes for c in ["code", "vb", "snippet", "clscode"])):
            self.in_code = True
            self.code_text = ""
            self.result.append("\n```vb\n")
        
        elif tag == "table":
            self.in_table = True
            self.current_table = []
        
        elif tag == "tr":
            self.current_row = []
        
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ["script", "style", "meta", "link", "title"]:
            self.skip_content = False
            return

        if tag in ["h1", "h2", "h3"]:
            self.result.append("\n")
        
        elif tag == "a":
            self.result.append("**")
        
        elif tag == "pre" or (self.in_code and tag == self.stack[-1]):
            # If we were in a code div/pre
            if self.in_code:
                self.result.append(self.code_text.strip())
                self.result.append("\n```\n")
                self.in_code = False
        
        elif tag == "table":
            self.in_table = False
            md_table = self._format_table()
            self.result.append(md_table)
        
        elif tag == "tr":
            if self.in_table:
                self.current_table.append(self.current_row)
        
        elif tag in ["td", "th"]:
            pass #Content handled in handle_data

        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.skip_content:
            return
        
        if self.in_code:
            self.code_text += data
        elif self.in_table:
            # We are inside a td/th likely
            if self.stack and self.stack[-1] in ["td", "th"]:
                self.current_row.append(data.strip().replace("|", "\\|"))
        else:
            # Clean up whitespace but keep some structure
            text = data.replace("\r", "").replace("\n", " ").strip()
            if text:
                # Add a leading space only if the previous part doesn't end with whitespace or a special char
                if self.result and not self.result[-1].endswith(("\n", " ", "#", "*")):
                    self.result.append(" ")
                self.result.append(text)

    def _format_table(self):
        if not self.current_table:
            return ""
        
        lines = []
        max_cols = max(len(row) for row in self.current_table)
        
        for i, row in enumerate(self.current_table):
            # Pad row
            row += [""] * (max_cols - len(row))
            lines.append("| " + " | ".join(row) + " |")
            if i == 0:
                lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        
        return "\n" + "\n".join(lines) + "\n"

    def get_markdown(self):
        return "".join(self.result)

class CHMConverter:
    def __init__(self, char_limit=500000, max_files=25):
        self.char_limit = char_limit
        self.max_files = max_files

    def decompile(self, chm_path, temp_dir):
        """Decompile CHM file using hh.exe."""
        print(f"Decompiling {chm_path} to {temp_dir}...")
        if os.name != 'nt':
            # Check if 7z is available as a fallback for non-Windows
            try:
                subprocess.run(["7z", "x", str(chm_path), f"-o{temp_dir}"], check=True, capture_output=True)
                print("Decompilation (via 7z) successful.")
                return True
            except:
                print("Warning: Currently running on a non-Windows OS and 7z failed.")
                print("Please use a Windows environment or extract the CHM manually.")
        
        try:
            # hh.exe -decompile <output_dir> <chm_file>
            subprocess.run(["hh.exe", "-decompile", str(temp_dir), str(chm_path)], check=True)
            print("Decompilation successful.")
        except Exception as e:
            print(f"Error during decompilation: {e}")
            return False
        return True

    def html_to_markdown(self, html_content, section_name):
        """Parse HTML and convert to Markdown based on specific requirements."""
        parser = SimpleHTMLToMD(section_name)
        try:
            parser.feed(html_content)
        except Exception as e:
            print(f"Warning: HTML parsing error: {e}")
        return parser.get_markdown()

    def process(self, source_chm, output_dir):
        # 1. Setup temp dir for decompilation
        temp_dir = Path("temp_decompiled")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)

        # 2. Decompile
        if not self.decompile(source_chm, temp_dir):
            print("Failed to decompile. Aborting.")
            return

        # 3. Collect and convert all HTML files
        all_md_contents = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.lower().endswith((".htm", ".html")):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(temp_dir)
                    section_name = str(rel_path.parent) if str(rel_path.parent) != "." else str(rel_path)
                    
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        md_text = self.html_to_markdown(content, section_name)
                        all_md_contents.append(md_text)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

        # 4. Aggregate contents
        self.save_aggregated(all_md_contents, output_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"Process complete. Output in: {output_dir}")

    def save_aggregated(self, contents, output_dir):
        """Merge contents into max 25 files, respecting character limits."""
        out_path = Path(output_dir)
        if out_path.exists():
            shutil.rmtree(out_path)
        out_path.mkdir(parents=True)

        total_chars = sum(len(c) for c in contents)
        print(f"Total processed characters: {total_chars}")
        
        # Target number of files: max 25
        # Ideal size per file: total_chars / 25
        ideal_size = max(total_chars // self.max_files, 1000) # Ensure non-zero
        chunk_size = min(ideal_size, self.char_limit)
        
        current_file_idx = 1
        current_content = []
        current_size = 0
        
        def flush(idx, data):
            filename = out_path / f"chm_content_{idx:02d}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(data))
            print(f"Saved: {filename} ({len(''.join(data))} chars)")

        for item in contents:
            if current_size + len(item) > chunk_size and current_content:
                if current_file_idx < self.max_files:
                    flush(current_file_idx, current_content)
                    current_file_idx += 1
                    current_content = [item]
                    current_size = len(item)
                else:
                    # If we already hit 25 files, append to the last one (unless it's truly massive)
                    current_content.append(item)
                    current_size += len(item)
            else:
                current_content.append(item)
                current_size += len(item)

        if current_content:
            flush(current_file_idx, current_content)

def main():
    parser = argparse.ArgumentParser(description="Convert VB6 CHM to Markdown for NotebookLM")
    parser.add_argument("source", help="Path to the .chm file")
    parser.add_argument("output", help="Output directory for .md files")
    parser.add_argument("--limit", type=int, default=500000, help="Character limit per file (default 500,000)")
    
    args = parser.parse_args()
    
    converter = CHMConverter(char_limit=args.limit)
    converter.process(args.source, args.output)

if __name__ == "__main__":
    main()
