import sys, os
sys.path.insert(0, os.getcwd())

import main
import customtkinter as ctk

print("=== TESTE RUNTIME: abrir_modal_resultados com binding FocusOut ===")

app = main.AppClinica()
app.after(1500, app.destroy)  # fecha sozinho

# Simular seleção de exames (par De Ritis + TG/HDL para testar os dois fluxos)
app.exames_selecionados_lista = ['EXM-AST-TGO', 'EXM-ALT-TGP', 'EXM-TRIGLICERIDEOS', 'EXM-HDL-COLESTEROL']
app.exames_solicitados = {}
app.resultados_lancados = {}

try:
    app.abrir_modal_resultados()
    print('[OK] abrir_modal_resultados() executou sem erros')
except Exception as e:
    print(f'[FALHA] abrir_modal_resultados(): {e}')
    raise

# Verificar estruturas criadas
entries = getattr(app, '_entries_resultados', {})
print(f'[INFO] entries criados: {list(entries.keys())}')

if len(entries) == 4:
    print('[OK] 4 entries registrados no dict')
else:
    print(f'[FALHA] esperava 4 entries, encontrei {len(entries)}')

# Verificar que cada entry tem o binding <FocusOut>
binds_ok = 0
for id_exame, (entry, lbl) in entries.items():
    info = entry.bind('<FocusOut>')
    if info:
        binds_ok += 1
    else:
        print(f'[FALHA] entry {id_exame} sem binding FocusOut')
print(f'[OK] bindings <FocusOut> presentes: {binds_ok}/{len(entries)}')

# Testar a chamada direta da função de avaliação (o que o FocusOut fará)
entry_tgo, lbl_tgo = entries['EXM-AST-TGO']
entry_tgp, lbl_tgp = entries['EXM-ALT-TGP']
entry_tgo.delete(0, 'end'); entry_tgo.insert(0, '45')
entry_tgp.delete(0, 'end'); entry_tgp.insert(0, '30')

# Simular o FocusOut no TGO
app._avaliar_entry_resultado(entry_tgo, lbl_tgo, 'EXM-AST-TGO')
status_tgo = lbl_tgo.cget('text')
print(f'[INFO] status TGO (valor 45): "{status_tgo}"')
if status_tgo and status_tgo != 'Valor inválido':
    print('[OK] avaliação individual atualizou a label imediatamente')
else:
    print('[FALHA] status não atualizado')

app.run()
print('RUNTIME OK')
