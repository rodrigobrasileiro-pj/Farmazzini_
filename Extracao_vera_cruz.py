import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Configurações de acesso
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

dados_produtos = []

for i in range(1, 220):
    url = f"https://www.drogariaveracruz.com.br/medicamentos/?p={i}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Localiza todos os containers de produtos na página atual
            div_elements = soup.find_all('div', class_='item-product')
            
            for item in div_elements:
                # Extração do Nome
                tag_nome = item.find('h2', class_='title')
                nome = tag_nome.get_text(strip=True) if tag_nome else "N/A"
                
                # Extração do Preço à Vista (Pix)
                tag_preco_pix = item.find('p', class_='seal-pix pix-price sale-price sale-price-pix money')
                if tag_preco_pix:
                    tag_strong_preco = tag_preco_pix.find('strong')
                    preco_vista = tag_strong_preco.get_text(strip=True) if tag_strong_preco else "Consultar"
                else:
                    preco_vista = "Consultar"

                # Extração da Qtd de Parcelas
                tag_qtd_parc = item.find('strong', class_='get_min_installments')
                qtd_parc = tag_qtd_parc.get_text(strip=True) if tag_qtd_parc else "1x"

                # Extração do Valor de Cada Parcela
                tag_val_parc = item.find('strong', class_='get_card_price')
                val_parc = tag_val_parc.get_text(strip=True) if tag_val_parc else preco_vista

                # Formatação solicitada: (número de parcelas x valor das parcelas)
                texto_parcelado = f"({qtd_parc} de {val_parc})"

                # Armazenamento temporário na lista
                dados_produtos.append({
                    'Medicamento': nome,
                    'Preço à Vista': preco_vista,
                    'Valor Parcelado': texto_parcelado
                })
            
            print(f"Página {i} processada com sucesso...")
        else:
            print(f"Erro na página {i}: Status {response.status_code}")
            
    except Exception as e:
        print(f"Falha na conexão da página {i}: {e}")
    
    # Pequena pausa para não sobrecarregar o servidor do site
    time.sleep(0.5)

# 2. Criação do DataFrame
df = pd.DataFrame(dados_produtos)

# 3. Tratamento de Duplicados
# Remove produtos que tenham o mesmo nome e preço exato
df_limpo = df.drop_duplicates(subset=['Medicamento', 'Preço à Vista']).reset_index(drop=True)

# 4. Resultado Final
print("-" * 30)
print(f"Total bruto capturado: {len(df)}")
print(f"Total após remover repetidos: {len(df_limpo)}")
print("-" * 30)

# Exportação para Excel/CSV
df_limpo.to_csv('lista_medicamentos.csv', index=False, encoding='utf-8-sig')
print("Arquivo 'lista_medicamentos.csv' gerado com sucesso!")