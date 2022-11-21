import glob
import os
import shutil

import pandas as pd

OFFSET = 600

class BibTexFormatter:
    def __init__(self) -> None:
        pass

    def format_bibtex(self):
        bibs = self._read_bibtex_from_file('in.bib')
        bibs = self.standard_author_name(bibs)

        df = self._write_bibtex(bibs, 'out.xlsx')
        self._rename_files(df)

    # ========== Utils ==========
    def _remove_up_to(self, in_string, chars, times):
        count_before = {c: 0 for c in set(chars)}
        count_after = {c: 0 for c in set(chars)}

        for cb in in_string:
            if cb not in chars or count_before[cb] >= times:
                break
            else:
                count_before[cb] += 1
        for ca in in_string[::-1]:
            if ca not in chars or count_after[ca] >= times:
                break
            else:
                count_after[ca] += 1

        num_to_cut_before = sum(count_before.values())
        num_to_cut_after = sum(count_after.values())

        return in_string[num_to_cut_before:-num_to_cut_after]

    # ========== IO ==========
    def _read_bibtex_from_file(self, in_file: str):
        with open(in_file, 'r') as f:
            lines = f.readlines()

        # add all bibtex entries to a dict with key=cite_name
        bibs = dict()
        previous_line = ""
        for line in lines:
            # skip comments and empty lines
            line = line.strip()
            if not line or line.startswith("%") or line.startswith("}"):
                continue

            line = f"{previous_line} {line}" if previous_line else line  # concatenate lines within a {}

            # find a new entry
            if line.startswith("@"):
                assert previous_line == ""
                cite_type, cite_name = line.split("{")
                entry = {"cite_type": cite_type.replace(',', '').strip()}
                bibs[cite_name.replace(',', '').strip()] = entry
                continue
            else:
                # inside an entry
                assert "=" in line
                if line.count("{") > line.count("}"):
                    previous_line = line
                    continue
                else:
                    previous_line = ""
                    key, value = line.split("=", 1)
                    entry[key.strip()] = self._remove_up_to(value.strip(), "{},", 1)

        return bibs
    
    def _write_bibtex(self, bibs, out_file):
        df = pd.DataFrame(columns=['title', 'author', 'venue'])
        for i, bib in enumerate(bibs.values()):
            if bib['cite_type'] == '@inproceedings':
                key_to_modify = 'booktitle'
            elif bib['cite_type'] == '@article':
                key_to_modify = 'journal'
            else:
                key_to_modify = None

            try:
                if key_to_modify is not None and key_to_modify in bib.keys():
                    bib_df = pd.DataFrame({'title': [f"{i+1+OFFSET}-{bib['title']}"], 'author': [bib['author']], 'venue': [bib[key_to_modify]]})
                else:
                    bib_df = pd.DataFrame({'title': [f"{i+1+OFFSET}-{bib['title']}"], 'author': [bib['author']], 'venue': [""]})
            except:
                print(bib)
                quit()
            df = df.append(bib_df)
        
        df.to_csv('out.csv', index=False, encoding='utf-8-sig')
        df.to_excel(out_file, index=False, encoding='utf-8-sig')
        
        return df
        
    def _rename_files(self, df):
        names = df['title'].tolist()
        print(len(names))
        
        os.makedirs('out_papers', exist_ok=True)
        files = glob.glob(os.path.expanduser("in_papers/*"))
        sorted_by_mtime_ascending = sorted(files, key=lambda t: os.stat(t).st_ctime)
        for i, name in enumerate(sorted_by_mtime_ascending):
            new_name = names[i]
            for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                new_name = new_name.replace(char, '_')
            new_name = new_name[:230]
            expansion_name = name.split('.')[-1]
            shutil.copyfile(name, f"out_papers/{new_name}.{expansion_name}")
    
    # ========== Formatters ==========
    def standard_author_name(self, bibs):
        for bib in bibs.values():
            authors = bib['author'].split("and")
            new_authors = ""
            for author in authors:
                author = author.strip()
                if "," in author:
                    author = author.split(",")
                    author = f"{author[1].strip()} {author[0].strip()}"
                new_authors += f"{author}, "
            new_authors = new_authors[:-2]
            bib['author'] = new_authors
        return bibs


formatter = BibTexFormatter()
formatter.format_bibtex()
