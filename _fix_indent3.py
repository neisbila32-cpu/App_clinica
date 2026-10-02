with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corregir indentacion de linha 1230 (entry)
if len(lines) > 1229 and 'entry = ctk.CTkEntry' in lines[1229]:
    lines[1229] = '            entry = ctk.CTkEntry(linha, placeholder_text="Resultado", width=140, font=ctk.CTkFont(size=15), fg_color="#ffffff", text_color="#1b5e20", placeholder_text_color="#7a9e7e", border_color="#a5d6a7")\n'
    print("[OK] Linha 1230 corregida")
else:
    print(f"[AVISO] Linha 1230 non atopada: '{lines[1229].rstrip() if len(lines)>1229 else 'EOF'}'")

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("[INFO] Arquivo guardado")
