from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# ---------------------------------------------------------------------------
# Seed data: ANVISA reference medications (Portaria 344 + tarjas) — 2026
# Format: (nome_comercial, registro_ms, principio_ativo, tarja,
#           uso_continuo, tipo_receita, lista_portaria)
# ---------------------------------------------------------------------------
_REFERENCIA_ANVISA = [

    # ── Analgésicos / Anti-inflamatórios ─────────────────────────────────────
    ('Dipirona 500mg',                '1.0783.0244.001', 'Dipirona Sódica',                    'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Dipirona 1g',                   '1.0783.0244.002', 'Dipirona Sódica',                    'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Paracetamol 500mg',             '1.0228.0025.001', 'Paracetamol',                        'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Paracetamol 750mg',             '1.0228.0025.002', 'Paracetamol',                        'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Ibuprofeno 400mg',              '1.0244.0120.001', 'Ibuprofeno',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Ibuprofeno 600mg',              '1.0244.0120.002', 'Ibuprofeno',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Naproxeno 500mg',               '1.0244.0167.001', 'Naproxeno Sódico',                   'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Diclofenaco Sódico 50mg',       '1.0244.0097.001', 'Diclofenaco Sódico',                 'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Diclofenaco Potássico 50mg',    '1.0244.0097.002', 'Diclofenaco Potássico',              'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Nimesulida 100mg',              '1.0244.0168.001', 'Nimesulida',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Meloxicam 7,5mg',               '1.0244.0148.001', 'Meloxicam',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Meloxicam 15mg',                '1.0244.0148.002', 'Meloxicam',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Celecoxibe 200mg',              '1.0244.0083.001', 'Celecoxibe',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Etoricoxibe 90mg',              '1.0244.0107.001', 'Etoricoxibe',                        'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Indometacina 25mg',             '1.0244.0130.001', 'Indometacina',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Piroxicam 20mg',                '1.0244.0182.001', 'Piroxicam',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Cetoprofeno 100mg',             '1.0244.0080.001', 'Cetoprofeno',                        'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Tenoxicam 20mg',                '1.0244.0231.001', 'Tenoxicam',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),

    # ── Controlados A1 – Entorpecentes mais rígidos ───────────────────────────
    ('Morfina 10mg/mL',               '1.0244.0162.001', 'Sulfato de Morfina',                 'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Morfina 30mg',                  '1.0244.0162.002', 'Sulfato de Morfina',                 'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Fentanila 50mcg/mL',            '1.0244.0112.001', 'Citrato de Fentanila',               'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Fentanila Adesivo 25mcg/h',     '1.0244.0112.002', 'Citrato de Fentanila',               'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A1'),
    ('Metadona 5mg',                  '1.0244.0149.001', 'Cloridrato de Metadona',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Metadona 10mg',                 '1.0244.0149.002', 'Cloridrato de Metadona',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Oxicodona 10mg',                '1.0244.0173.001', 'Cloridrato de Oxicodona',            'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Oxicodona 20mg',                '1.0244.0173.002', 'Cloridrato de Oxicodona',            'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Oxicodona 40mg',                '1.0244.0173.003', 'Cloridrato de Oxicodona',            'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Codeína 30mg',                  '1.0244.0089.001', 'Fosfato de Codeína',                 'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Sufentanila 50mcg/mL',          '1.0244.0227.001', 'Citrato de Sufentanila',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Hidromorfona 2mg',              '1.0244.0128.001', 'Cloridrato de Hidromorfona',         'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),
    ('Petidina 50mg/mL',              '1.0244.0179.001', 'Cloridrato de Petidina',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A1'),

    # ── Controlados A2 – Entorpecentes de uso especial ───────────────────────
    ('Tramadol 50mg',                 '1.0244.0232.001', 'Cloridrato de Tramadol',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A2'),
    ('Tramadol 100mg',                '1.0244.0232.002', 'Cloridrato de Tramadol',             'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A2'),
    ('Buprenorfina 0,2mg',            '1.0244.0059.001', 'Cloridrato de Buprenorfina',         'Portaria 344',   False, "Receita 'A' (Amarela)",                     'A2'),
    ('Buprenorfina 8mg SL',           '1.0244.0059.002', 'Cloridrato de Buprenorfina',         'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A2'),

    # ── Controlados A3 – Psicotrópicos Notificação A ─────────────────────────
    ('Metilfenidato 10mg',            '1.0244.0151.001', 'Cloridrato de Metilfenidato',        'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Metilfenidato 20mg',            '1.0244.0151.002', 'Cloridrato de Metilfenidato',        'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Lisdexanfetamina 20mg',         '1.0244.0143.001', 'Dimesilato de Lisdexanfetamina',     'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Lisdexanfetamina 30mg',         '1.0244.0143.002', 'Dimesilato de Lisdexanfetamina',     'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Lisdexanfetamina 50mg',         '1.0244.0143.003', 'Dimesilato de Lisdexanfetamina',     'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Lisdexanfetamina 70mg',         '1.0244.0143.004', 'Dimesilato de Lisdexanfetamina',     'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Modafinila 100mg',              '1.0244.0159.001', 'Modafinila',                         'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),
    ('Modafinila 200mg',              '1.0244.0159.002', 'Modafinila',                         'Portaria 344',   True,  "Receita 'A' (Amarela)",                     'A3'),

    # ── Controlados B1 – Psicotrópicos com potencial de dependência ──────────
    ('Alprazolam 0,25mg',             '1.0244.0021.001', 'Alprazolam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Alprazolam 0,5mg',              '1.0244.0021.002', 'Alprazolam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Alprazolam 1mg',                '1.0244.0021.003', 'Alprazolam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Alprazolam 2mg',                '1.0244.0021.004', 'Alprazolam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Diazepam 5mg',                  '1.0244.0096.001', 'Diazepam',                           'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Diazepam 10mg',                 '1.0244.0096.002', 'Diazepam',                           'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Clonazepam 0,5mg',              '1.0244.0088.001', 'Clonazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Clonazepam 2mg',                '1.0244.0088.002', 'Clonazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Clonazepam Gotas',              '1.0244.0088.003', 'Clonazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Lorazepam 1mg',                 '1.0244.0145.001', 'Lorazepam',                          'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Lorazepam 2mg',                 '1.0244.0145.002', 'Lorazepam',                          'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Bromazepam 3mg',                '1.0244.0058.001', 'Bromazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Bromazepam 6mg',                '1.0244.0058.002', 'Bromazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Nitrazepam 5mg',                '1.0244.0169.001', 'Nitrazepam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Midazolam 7,5mg',               '1.0244.0156.001', 'Maleato de Midazolam',               'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Midazolam 15mg',                '1.0244.0156.002', 'Maleato de Midazolam',               'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Zolpidem 10mg',                 '1.0244.0241.001', 'Tartarato de Zolpidem',              'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Zopiclona 7,5mg',               '1.0244.0242.001', 'Zopiclona',                          'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Clobazam 10mg',                 '1.0244.0087.001', 'Clobazam',                           'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Clobazam 20mg',                 '1.0244.0087.002', 'Clobazam',                           'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Cloxazolam 2mg',                '1.0244.0091.001', 'Cloxazolam',                         'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Flunitrazepam 1mg',             '1.0244.0116.001', 'Flunitrazepam',                      'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Estazolam 2mg',                 '1.0244.0106.001', 'Estazolam',                          'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Oxazepam 15mg',                 '1.0244.0172.001', 'Oxazepam',                           'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Eszopiclona 3mg',               '1.0244.0108.001', 'Eszopiclona',                        'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Alfazolam 0,5mg',               '1.0244.0020.001', 'Alfazolam',                          'Portaria 344',   True,  "Receita 'B' Especial (Azul)",               'B1'),
    ('Flurazepam 15mg',               '1.0244.0118.001', 'Cloridrato de Flurazepam',           'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),
    ('Halazepam 40mg',                '1.0244.0125.001', 'Halazepam',                          'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B1'),

    # ── Controlados B2 – Anorexígenos ────────────────────────────────────────
    ('Femproporex 25mg',              '1.0244.0111.001', 'Femproporex',                        'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B2'),
    ('Sibutramina 10mg',              '1.0244.0225.001', 'Cloridrato de Sibutramina',          'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B2'),
    ('Sibutramina 15mg',              '1.0244.0225.002', 'Cloridrato de Sibutramina',          'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B2'),
    ('Fentermina 30mg',               '1.0244.0113.001', 'Cloridrato de Fentermina',           'Portaria 344',   False, "Receita 'B' Especial (Azul)",               'B2'),

    # ── Controlados C1 – Outras substâncias de controle especial ─────────────
    ('Fluoxetina 20mg',               '1.0244.0117.001', 'Cloridrato de Fluoxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Fluoxetina 40mg',               '1.0244.0117.002', 'Cloridrato de Fluoxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Sertralina 50mg',               '1.0244.0224.001', 'Cloridrato de Sertralina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Sertralina 100mg',              '1.0244.0224.002', 'Cloridrato de Sertralina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Amitriptilina 25mg',            '1.0228.0011.001', 'Cloridrato de Amitriptilina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Amitriptilina 75mg',            '1.0228.0011.002', 'Cloridrato de Amitriptilina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Nortriptilina 25mg',            '1.0244.0170.001', 'Cloridrato de Nortriptilina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Nortriptilina 50mg',            '1.0244.0170.002', 'Cloridrato de Nortriptilina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Nortriptilina 75mg',            '1.0244.0170.003', 'Cloridrato de Nortriptilina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Venlafaxina 75mg',              '1.0244.0237.001', 'Cloridrato de Venlafaxina',          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Venlafaxina 150mg',             '1.0244.0237.002', 'Cloridrato de Venlafaxina',          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Duloxetina 30mg',               '1.0244.0103.001', 'Cloridrato de Duloxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Duloxetina 60mg',               '1.0244.0103.002', 'Cloridrato de Duloxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Escitalopram 10mg',             '1.0244.0105.001', 'Oxalato de Escitalopram',            'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Escitalopram 20mg',             '1.0244.0105.002', 'Oxalato de Escitalopram',            'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Paroxetina 20mg',               '1.0244.0176.001', 'Cloridrato de Paroxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Paroxetina 40mg',               '1.0244.0176.002', 'Cloridrato de Paroxetina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Citalopram 20mg',               '1.0244.0085.001', 'Hidrobrometo de Citalopram',         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Citalopram 40mg',               '1.0244.0085.002', 'Hidrobrometo de Citalopram',         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Clomipramina 25mg',             '1.0244.0090.001', 'Cloridrato de Clomipramina',         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Clomipramina 75mg',             '1.0244.0090.002', 'Cloridrato de Clomipramina',         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Mirtazapina 15mg',              '1.0244.0157.001', 'Mirtazapina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Mirtazapina 30mg',              '1.0244.0157.002', 'Mirtazapina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Mirtazapina 45mg',              '1.0244.0157.003', 'Mirtazapina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Bupropiona 150mg',              '1.0244.0060.001', 'Cloridrato de Bupropiona',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Bupropiona 300mg',              '1.0244.0060.002', 'Cloridrato de Bupropiona',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Quetiapina 25mg',               '1.0244.0191.001', 'Fumarato de Quetiapina',             'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Quetiapina 100mg',              '1.0244.0191.002', 'Fumarato de Quetiapina',             'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Quetiapina 200mg',              '1.0244.0191.003', 'Fumarato de Quetiapina',             'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Quetiapina 300mg',              '1.0244.0191.004', 'Fumarato de Quetiapina',             'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Risperidona 1mg',               '1.0244.0202.001', 'Risperidona',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Risperidona 2mg',               '1.0244.0202.002', 'Risperidona',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Risperidona 3mg',               '1.0244.0202.003', 'Risperidona',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Olanzapina 5mg',                '1.0244.0171.001', 'Olanzapina',                         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Olanzapina 10mg',               '1.0244.0171.002', 'Olanzapina',                         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Haloperidol 1mg',               '1.0244.0126.001', 'Haloperidol',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Haloperidol 5mg',               '1.0244.0126.002', 'Haloperidol',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Carbamazepina 200mg',           '1.0244.0069.001', 'Carbamazepina',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Carbamazepina 400mg',           '1.0244.0069.002', 'Carbamazepina',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Ácido Valproico 250mg',         '1.0244.0017.001', 'Ácido Valproico',                    'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Ácido Valproico 500mg',         '1.0244.0017.002', 'Ácido Valproico',                    'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Ácido Valproico 600mg',         '1.0244.0017.003', 'Ácido Valproico',                    'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Gabapentina 300mg',             '1.0244.0120.003', 'Gabapentina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Gabapentina 400mg',             '1.0244.0120.004', 'Gabapentina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Pregabalina 75mg',              '1.0244.0187.001', 'Pregabalina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Pregabalina 150mg',             '1.0244.0187.002', 'Pregabalina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Pregabalina 300mg',             '1.0244.0187.003', 'Pregabalina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lamotrigina 25mg',              '1.0244.0142.001', 'Lamotrigina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lamotrigina 50mg',              '1.0244.0142.002', 'Lamotrigina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lamotrigina 100mg',             '1.0244.0142.003', 'Lamotrigina',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Topiramato 25mg',               '1.0244.0231.001', 'Topiramato',                         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Topiramato 50mg',               '1.0244.0231.002', 'Topiramato',                         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Topiramato 100mg',              '1.0244.0231.003', 'Topiramato',                         'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Fenobarbital 50mg',             '1.0244.0114.001', 'Fenobarbital',                       'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Fenobarbital 100mg',            '1.0244.0114.002', 'Fenobarbital',                       'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Fenitoína 100mg',               '1.0244.0115.001', 'Fenitoína Sódica',                   'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Levetiracetam 250mg',           '1.0244.0141.001', 'Levetiracetam',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Levetiracetam 500mg',           '1.0244.0141.002', 'Levetiracetam',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Levetiracetam 1000mg',          '1.0244.0141.003', 'Levetiracetam',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lítio 300mg',                   '1.0244.0144.001', 'Carbonato de Lítio',                 'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lítio 450mg',                   '1.0244.0144.002', 'Carbonato de Lítio',                 'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Aripiprazol 10mg',              '1.0244.0031.001', 'Aripiprazol',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Aripiprazol 15mg',              '1.0244.0031.002', 'Aripiprazol',                        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Clozapina 25mg',                '1.0244.0092.001', 'Clozapina',                          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Clozapina 100mg',               '1.0244.0092.002', 'Clozapina',                          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Ziprasidona 40mg',              '1.0244.0240.001', 'Cloridrato de Ziprasidona',          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Ziprasidona 80mg',              '1.0244.0240.002', 'Cloridrato de Ziprasidona',          'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Paliperidona 3mg',              '1.0244.0174.001', 'Paliperidona',                       'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Paliperidona 6mg',              '1.0244.0174.002', 'Paliperidona',                       'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Desvenlafaxina 50mg',           '1.0244.0095.001', 'Succinato de Desvenlafaxina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Desvenlafaxina 100mg',          '1.0244.0095.002', 'Succinato de Desvenlafaxina',        'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Oxcarbazepina 300mg',           '1.0244.0173.004', 'Oxcarbazepina',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Oxcarbazepina 600mg',           '1.0244.0173.005', 'Oxcarbazepina',                      'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Imipramina 25mg',               '1.0244.0129.001', 'Cloridrato de Imipramina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Imipramina 75mg',               '1.0244.0129.002', 'Cloridrato de Imipramina',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lurasidona 40mg',               '1.0244.0147.001', 'Cloridrato de Lurasidona',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Lurasidona 80mg',               '1.0244.0147.002', 'Cloridrato de Lurasidona',           'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),
    ('Asenapina 5mg',                 '1.0244.0032.001', 'Maleato de Asenapina',               'Portaria 344',   True,  'Receita de Controle Especial (Branca)',      'C1'),

    # ── Controlados C2 – Substâncias retinóicas ───────────────────────────────
    ('Isotretinoína 10mg',            '1.0244.0135.001', 'Isotretinoína',                      'Portaria 344',   False, 'Receita de Controle Especial (Branca)',      'C2'),
    ('Isotretinoína 20mg',            '1.0244.0135.002', 'Isotretinoína',                      'Portaria 344',   False, 'Receita de Controle Especial (Branca)',      'C2'),
    ('Isotretinoína 40mg',            '1.0244.0135.003', 'Isotretinoína',                      'Portaria 344',   False, 'Receita de Controle Especial (Branca)',      'C2'),
    ('Acitretina 10mg',               '1.0244.0018.001', 'Acitretina',                         'Portaria 344',   False, 'Receita de Controle Especial (Branca)',      'C2'),
    ('Acitretina 25mg',               '1.0244.0018.002', 'Acitretina',                         'Portaria 344',   False, 'Receita de Controle Especial (Branca)',      'C2'),

    # ── Cardiovascular ────────────────────────────────────────────────────────
    ('Atenolol 25mg',                 '1.0228.0038.001', 'Atenolol',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atenolol 50mg',                 '1.0228.0038.002', 'Atenolol',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atenolol 100mg',                '1.0228.0038.003', 'Atenolol',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metoprolol 25mg',               '1.0244.0150.001', 'Succinato de Metoprolol',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metoprolol 50mg',               '1.0244.0150.002', 'Succinato de Metoprolol',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metoprolol 100mg',              '1.0244.0150.003', 'Succinato de Metoprolol',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Carvedilol 6,25mg',             '1.0244.0072.001', 'Carvedilol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Carvedilol 12,5mg',             '1.0244.0072.002', 'Carvedilol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Carvedilol 25mg',               '1.0244.0072.003', 'Carvedilol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Propranolol 10mg',              '1.0244.0189.001', 'Cloridrato de Propranolol',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Propranolol 40mg',              '1.0244.0189.002', 'Cloridrato de Propranolol',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Bisoprolol 2,5mg',              '1.0244.0054.001', 'Fumarato de Bisoprolol',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Bisoprolol 5mg',                '1.0244.0054.002', 'Fumarato de Bisoprolol',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Bisoprolol 10mg',               '1.0244.0054.003', 'Fumarato de Bisoprolol',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Losartana 25mg',                '1.0558.0512.001', 'Losartana Potássica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Losartana 50mg',                '1.0558.0512.002', 'Losartana Potássica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Valsartana 80mg',               '1.0244.0236.001', 'Valsartana',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Valsartana 160mg',              '1.0244.0236.002', 'Valsartana',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Valsartana 320mg',              '1.0244.0236.003', 'Valsartana',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Telmisartana 40mg',             '1.0244.0229.001', 'Telmisartana',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Telmisartana 80mg',             '1.0244.0229.002', 'Telmisartana',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Olmesartana 20mg',              '1.0244.0172.002', 'Medoxomila de Olmesartana',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Olmesartana 40mg',              '1.0244.0172.003', 'Medoxomila de Olmesartana',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Enalapril 5mg',                 '1.0244.0104.003', 'Maleato de Enalapril',               'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Enalapril 10mg',                '1.0244.0104.004', 'Maleato de Enalapril',               'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Enalapril 20mg',                '1.0244.0104.005', 'Maleato de Enalapril',               'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Captopril 25mg',                '1.0228.0047.001', 'Captopril',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Captopril 50mg',                '1.0228.0047.002', 'Captopril',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ramipril 2,5mg',                '1.0244.0196.001', 'Ramipril',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ramipril 5mg',                  '1.0244.0196.002', 'Ramipril',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ramipril 10mg',                 '1.0244.0196.003', 'Ramipril',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Lisinopril 5mg',                '1.0244.0143.005', 'Lisinopril',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Lisinopril 10mg',               '1.0244.0143.006', 'Lisinopril',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Lisinopril 20mg',               '1.0244.0143.007', 'Lisinopril',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Amlodipina 5mg',                '1.0244.0026.001', 'Besilato de Amlodipina',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Amlodipina 10mg',               '1.0244.0026.002', 'Besilato de Amlodipina',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Nifedipino 10mg',               '1.0244.0167.002', 'Nifedipino',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Nifedipino 20mg',               '1.0244.0167.003', 'Nifedipino',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Verapamil 80mg',                '1.0244.0238.001', 'Cloridrato de Verapamil',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Diltiazem 30mg',                '1.0244.0099.001', 'Cloridrato de Diltiazem',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Diltiazem 60mg',                '1.0244.0099.002', 'Cloridrato de Diltiazem',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Hidroclorotiazida 25mg',        '1.0244.0127.001', 'Hidroclorotiazida',                  'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Furosemida 40mg',               '1.0244.0119.001', 'Furosemida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Espironolactona 25mg',          '1.0244.0108.002', 'Espironolactona',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Espironolactona 50mg',          '1.0244.0108.003', 'Espironolactona',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Espironolactona 100mg',         '1.0244.0108.004', 'Espironolactona',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Indapamida 1,5mg',              '1.0244.0131.001', 'Indapamida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Clortalidona 12,5mg',           '1.0244.0086.001', 'Clortalidona',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Clortalidona 25mg',             '1.0244.0086.002', 'Clortalidona',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Digoxina 0,25mg',               '1.0244.0098.001', 'Digoxina',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Amiodarona 100mg',              '1.0244.0025.001', 'Cloridrato de Amiodarona',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Amiodarona 200mg',              '1.0244.0025.002', 'Cloridrato de Amiodarona',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Sinvastatina 10mg',             '1.0244.0244.001', 'Sinvastatina',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Sinvastatina 20mg',             '1.0244.0244.002', 'Sinvastatina',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Sinvastatina 40mg',             '1.0244.0244.003', 'Sinvastatina',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atorvastatina 10mg',            '1.0244.0037.001', 'Atorvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atorvastatina 20mg',            '1.0244.0037.002', 'Atorvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atorvastatina 40mg',            '1.0244.0037.003', 'Atorvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Atorvastatina 80mg',            '1.0244.0037.004', 'Atorvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rosuvastatina 5mg',             '1.0244.0206.001', 'Rosuvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rosuvastatina 10mg',            '1.0244.0206.002', 'Rosuvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rosuvastatina 20mg',            '1.0244.0206.003', 'Rosuvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rosuvastatina 40mg',            '1.0244.0206.004', 'Rosuvastatina Cálcica',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ezetimiba 10mg',                '1.0244.0110.001', 'Ezetimiba',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('AAS 100mg',                     '1.0228.0001.001', 'Ácido Acetilsalicílico',             'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Clopidogrel 75mg',              '1.0244.0088.004', 'Clopidogrel',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Varfarina 1mg',                 '1.0244.0239.001', 'Varfarina Sódica',                   'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Varfarina 5mg',                 '1.0244.0239.002', 'Varfarina Sódica',                   'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivaroxabana 10mg',             '1.0244.0203.001', 'Rivaroxabana',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivaroxabana 15mg',             '1.0244.0203.002', 'Rivaroxabana',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivaroxabana 20mg',             '1.0244.0203.003', 'Rivaroxabana',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Apixabana 2,5mg',               '1.0244.0030.001', 'Apixabana',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Apixabana 5mg',                 '1.0244.0030.002', 'Apixabana',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Dabigatrana 110mg',             '1.0244.0093.001', 'Etexilato de Dabigatrana',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Dabigatrana 150mg',             '1.0244.0093.002', 'Etexilato de Dabigatrana',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ivabradina 5mg',                '1.0244.0136.001', 'Cloridrato de Ivabradina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ivabradina 7,5mg',              '1.0244.0136.002', 'Cloridrato de Ivabradina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),

    # ── Endócrino / Diabetes ──────────────────────────────────────────────────
    ('Metformina 500mg',              '1.0228.0132.001', 'Cloridrato de Metformina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metformina 850mg',              '1.0228.0132.002', 'Cloridrato de Metformina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metformina 1000mg',             '1.0228.0132.003', 'Cloridrato de Metformina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Glibenclamida 5mg',             '1.0244.0121.001', 'Glibenclamida',                      'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Glimepirida 1mg',               '1.0244.0122.001', 'Glimepirida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Glimepirida 2mg',               '1.0244.0122.002', 'Glimepirida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Glimepirida 4mg',               '1.0244.0122.003', 'Glimepirida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Gliclazida 30mg MR',            '1.0244.0123.001', 'Gliclazida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Gliclazida 60mg MR',            '1.0244.0123.002', 'Gliclazida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Sitagliptina 100mg',            '1.0244.0226.001', 'Fosfato de Sitagliptina',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Vildagliptina 50mg',            '1.0244.0238.002', 'Vildagliptina',                      'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Saxagliptina 5mg',              '1.0244.0220.001', 'Cloridrato de Saxagliptina',         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Empagliflozina 10mg',           '1.0244.0104.006', 'Empagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Empagliflozina 25mg',           '1.0244.0104.007', 'Empagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Dapagliflozina 5mg',            '1.0244.0094.001', 'Dapagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Dapagliflozina 10mg',           '1.0244.0094.002', 'Dapagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Canagliflozina 100mg',          '1.0244.0066.001', 'Canagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Canagliflozina 300mg',          '1.0244.0066.002', 'Canagliflozina',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina Regular 100UI/mL',     '1.0244.0133.001', 'Insulina Humana Regular',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina NPH 100UI/mL',         '1.0244.0133.002', 'Insulina Humana NPH',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina Glargina 100UI/mL',    '1.0244.0133.003', 'Insulina Glargina',                  'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina Detemir 100UI/mL',     '1.0244.0133.004', 'Insulina Detemir',                   'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina Aspart 100UI/mL',      '1.0244.0133.005', 'Insulina Aspart',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Insulina Lispro 100UI/mL',      '1.0244.0133.006', 'Insulina Lispro',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Levotiroxina 25mcg',            '1.0228.0124.001', 'Levotiroxina Sódica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Levotiroxina 50mcg',            '1.0228.0124.002', 'Levotiroxina Sódica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Levotiroxina 75mcg',            '1.0228.0124.003', 'Levotiroxina Sódica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Levotiroxina 100mcg',           '1.0228.0124.004', 'Levotiroxina Sódica',                'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metimazol 5mg',                 '1.0244.0152.001', 'Metimazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metimazol 10mg',                '1.0244.0152.002', 'Metimazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Propiltiouracil 100mg',         '1.0244.0190.001', 'Propiltiouracil',                    'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Prednisona 5mg',                '1.0244.0185.001', 'Prednisona',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Prednisona 20mg',               '1.0244.0185.002', 'Prednisona',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Prednisolona 5mg',              '1.0244.0186.001', 'Prednisolona',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Prednisolona 20mg',             '1.0244.0186.002', 'Prednisolona',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Dexametasona 4mg',              '1.0244.0096.003', 'Dexametasona',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Hidrocortisona 20mg',           '1.0244.0127.002', 'Hidrocortisona',                     'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),

    # ── Gastrointestinais ─────────────────────────────────────────────────────
    ('Omeprazol 10mg',                '1.0558.0380.001', 'Omeprazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Omeprazol 20mg',                '1.0558.0380.002', 'Omeprazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Omeprazol 40mg',                '1.0558.0380.003', 'Omeprazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Pantoprazol 20mg',              '1.0244.0175.001', 'Pantoprazol Sódico',                 'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Pantoprazol 40mg',              '1.0244.0175.002', 'Pantoprazol Sódico',                 'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Esomeprazol 20mg',              '1.0244.0107.001', 'Esomeprazol Magnésico',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Esomeprazol 40mg',              '1.0244.0107.002', 'Esomeprazol Magnésico',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rabeprazol 20mg',               '1.0244.0195.001', 'Rabeprazol Sódico',                  'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Famotidina 20mg',               '1.0244.0110.002', 'Famotidina',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Famotidina 40mg',               '1.0244.0110.003', 'Famotidina',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Domperidona 10mg',              '1.0244.0101.001', 'Domperidona',                        'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Metoclopramida 10mg',           '1.0244.0153.001', 'Cloridrato de Metoclopramida',       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Ondansetrona 4mg',              '1.0244.0171.003', 'Cloridrato de Ondansetrona',         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Ondansetrona 8mg',              '1.0244.0171.004', 'Cloridrato de Ondansetrona',         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Simeticona 80mg',               '1.0244.0223.001', 'Simeticona',                         'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Hioscina Butilbrometo 10mg',    '1.0244.0127.003', 'Butilbrometo de Escopolamina',       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Loperamida 2mg',                '1.0244.0145.003', 'Cloridrato de Loperamida',           'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Bisacodil 5mg',                 '1.0244.0055.001', 'Bisacodil',                          'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Lactulose 667mg/mL',            '1.0244.0140.001', 'Lactulose',                          'Sem Tarja',      True,  'Receita Simples',                           None),

    # ── Antibióticos ──────────────────────────────────────────────────────────
    ('Amoxicilina 250mg',             '1.0558.0064.001', 'Amoxicilina Tri-Hidratada',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Amoxicilina 500mg',             '1.0558.0064.002', 'Amoxicilina Tri-Hidratada',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Amoxicilina 875mg',             '1.0558.0064.003', 'Amoxicilina Tri-Hidratada',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Amoxicilina + Clavulanato 500/125mg','1.0558.0064.004','Amoxicilina + Clavulanato de Potássio','Tarja Vermelha',False,'Receita de Controle Especial (Branca)',  None),
    ('Amoxicilina + Clavulanato 875/125mg','1.0558.0064.005','Amoxicilina + Clavulanato de Potássio','Tarja Vermelha',False,'Receita de Controle Especial (Branca)',  None),
    ('Azitromicina 250mg',            '1.0244.0281.001', 'Azitromicina Di-Hidratada',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Azitromicina 500mg',            '1.0244.0281.002', 'Azitromicina Di-Hidratada',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Claritromicina 250mg',          '1.0244.0086.003', 'Claritromicina',                     'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Claritromicina 500mg',          '1.0244.0086.004', 'Claritromicina',                     'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Ciprofloxacino 500mg',          '1.0244.0084.001', 'Cloridrato de Ciprofloxacino',       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Ciprofloxacino 750mg',          '1.0244.0084.002', 'Cloridrato de Ciprofloxacino',       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Levofloxacino 500mg',           '1.0244.0141.004', 'Levofloxacino',                      'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Levofloxacino 750mg',           '1.0244.0141.005', 'Levofloxacino',                      'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Moxifloxacino 400mg',           '1.0244.0163.001', 'Cloridrato de Moxifloxacino',        'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Cefalexina 250mg',              '1.0244.0079.001', 'Cefalexina',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Cefalexina 500mg',              '1.0244.0079.002', 'Cefalexina',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Cefuroxima 250mg',              '1.0244.0082.001', 'Cefuroxima Axetila',                 'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Cefuroxima 500mg',              '1.0244.0082.002', 'Cefuroxima Axetila',                 'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Doxiciclina 100mg',             '1.0244.0102.001', 'Cloridrato de Doxiciclina',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Metronidazol 250mg',            '1.0244.0155.001', 'Metronidazol',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Metronidazol 400mg',            '1.0244.0155.002', 'Metronidazol',                       'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('SMX+TMP 400/80mg',              '1.0244.0228.002', 'Sulfametoxazol + Trimetoprima',      'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('SMX+TMP 800/160mg',             '1.0244.0228.003', 'Sulfametoxazol + Trimetoprima',      'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Nitrofurantoína 100mg',         '1.0244.0168.002', 'Nitrofurantoína',                    'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Rifampicina 300mg',             '1.0244.0200.001', 'Rifampicina',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Isoniazida 100mg',              '1.0244.0132.001', 'Isoniazida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Isoniazida 300mg',              '1.0244.0132.002', 'Isoniazida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Pirazinamida 500mg',            '1.0244.0183.001', 'Pirazinamida',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Etambutol 400mg',               '1.0244.0109.001', 'Cloridrato de Etambutol',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),

    # ── Respiratório ──────────────────────────────────────────────────────────
    ('Salbutamol 100mcg',             '1.0244.0214.001', 'Sulfato de Salbutamol',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Formoterol 12mcg',              '1.0244.0118.002', 'Fumarato de Formoterol',             'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Salmeterol 50mcg',              '1.0244.0215.001', 'Xinafoato de Salmeterol',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Budesonida 200mcg',             '1.0244.0059.003', 'Budesonida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Budesonida 400mcg',             '1.0244.0059.004', 'Budesonida',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Fluticasona 50mcg',             '1.0244.0118.003', 'Propionato de Fluticasona',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Fluticasona 125mcg',            '1.0244.0118.004', 'Propionato de Fluticasona',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Fluticasona 250mcg',            '1.0244.0118.005', 'Propionato de Fluticasona',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Beclometasona 100mcg',          '1.0244.0050.001', 'Dipropionato de Beclometasona',      'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Montelucaste 5mg',              '1.0244.0161.001', 'Sódio de Montelucaste',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Montelucaste 10mg',             '1.0244.0161.002', 'Sódio de Montelucaste',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Ipratrópio 20mcg',              '1.0244.0132.003', 'Brometo de Ipratrópio',              'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Tiotrópio 18mcg',               '1.0244.0232.003', 'Brometo de Tiotrópio',               'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Acetilcisteína 600mg',          '1.0244.0015.001', 'N-Acetilcisteína',                   'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Ambroxol 30mg',                 '1.0244.0024.001', 'Cloridrato de Ambroxol',             'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Cetirizina 10mg',               '1.0244.0078.001', 'Cloridrato de Cetirizina',           'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Loratadina 10mg',               '1.0244.0146.001', 'Loratadina',                         'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Fexofenadina 60mg',             '1.0244.0112.003', 'Cloridrato de Fexofenadina',         'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Fexofenadina 120mg',            '1.0244.0112.004', 'Cloridrato de Fexofenadina',         'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Fexofenadina 180mg',            '1.0244.0112.005', 'Cloridrato de Fexofenadina',         'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Desloratadina 5mg',             '1.0244.0095.003', 'Desloratadina',                      'Sem Tarja',      False, 'Receita Simples',                           None),
    ('Bilastina 20mg',                '1.0244.0053.001', 'Bilastina',                          'Sem Tarja',      False, 'Receita Simples',                           None),

    # ── Neurológico ───────────────────────────────────────────────────────────
    ('Sumatriptana 50mg',             '1.0244.0227.001', 'Succinato de Sumatriptana',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Sumatriptana 100mg',            '1.0244.0227.002', 'Succinato de Sumatriptana',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Flunarizina 5mg',               '1.0244.0117.002', 'Cloridrato de Flunarizina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Betaistina 8mg',                '1.0244.0052.001', 'Cloridrato de Betaistina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Betaistina 16mg',               '1.0244.0052.002', 'Cloridrato de Betaistina',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Donepezila 5mg',                '1.0244.0101.002', 'Cloridrato de Donepezila',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Donepezila 10mg',               '1.0244.0101.003', 'Cloridrato de Donepezila',           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Memantina 10mg',                '1.0244.0148.003', 'Cloridrato de Memantina',            'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivastigmina 1,5mg',            '1.0244.0204.001', 'Tartarato de Rivastigmina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivastigmina 3mg',              '1.0244.0204.002', 'Tartarato de Rivastigmina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivastigmina 4,5mg',            '1.0244.0204.003', 'Tartarato de Rivastigmina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Rivastigmina 6mg',              '1.0244.0204.004', 'Tartarato de Rivastigmina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),

    # ── Oncológico / Reumatologia ─────────────────────────────────────────────
    ('Tamoxifeno 20mg',               '1.0244.0228.004', 'Tamoxifeno',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Anastrozol 1mg',                '1.0244.0029.001', 'Anastrozol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Letrozol 2,5mg',                '1.0244.0141.006', 'Letrozol',                           'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Capecitabina 500mg',            '1.0244.0067.001', 'Capecitabina',                       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Metotrexato 2,5mg',             '1.0244.0153.002', 'Metotrexato',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Hidroxicloroquina 200mg',       '1.0244.0128.002', 'Sulfato de Hidroxicloroquina',       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Hidroxicloroquina 400mg',       '1.0244.0128.003', 'Sulfato de Hidroxicloroquina',       'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Leflunomida 10mg',              '1.0244.0141.007', 'Leflunomida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Leflunomida 20mg',              '1.0244.0141.008', 'Leflunomida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Alopurinol 100mg',              '1.0228.0010.001', 'Alopurinol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Alopurinol 300mg',              '1.0228.0010.002', 'Alopurinol',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Colchicina 0,5mg',              '1.0244.0089.002', 'Colchicina',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),

    # ── Urologia ─────────────────────────────────────────────────────────────
    ('Sildenafila 50mg',              '1.0244.0222.001', 'Citrato de Sildenafila',             'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Sildenafila 100mg',             '1.0244.0222.002', 'Citrato de Sildenafila',             'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Tadalafila 5mg',                '1.0244.0228.005', 'Tadalafila',                         'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Tadalafila 20mg',               '1.0244.0228.006', 'Tadalafila',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Finasterida 5mg',               '1.0244.0113.001', 'Finasterida',                        'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
    ('Tamsulosina 0,4mg',             '1.0244.0229.002', 'Cloridrato de Tamsulosina',          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),

    # ── Antivirais / Antifúngicos / Dermatologia ─────────────────────────────
    ('Aciclovir 200mg',               '1.0244.0016.001', 'Aciclovir',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Aciclovir 400mg',               '1.0244.0016.002', 'Aciclovir',                          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Valaciclovir 500mg',            '1.0244.0235.001', 'Cloridrato de Valaciclovir',         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Valaciclovir 1000mg',           '1.0244.0235.002', 'Cloridrato de Valaciclovir',         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Fluconazol 150mg',              '1.0244.0116.002', 'Fluconazol',                         'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Itraconazol 100mg',             '1.0244.0135.004', 'Itraconazol',                        'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),
    ('Terbinafina 250mg',             '1.0244.0230.001', 'Cloridrato de Terbinafina',          'Tarja Vermelha', False, 'Receita de Controle Especial (Branca)',      None),

    # ── Outros ────────────────────────────────────────────────────────────────
    ('Ácido Fólico 5mg',              '1.0228.0006.001', 'Ácido Fólico',                       'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Sulfato Ferroso 40mg',          '1.0228.0042.001', 'Sulfato Ferroso',                    'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Vitamina D3 1000UI',            '1.0244.0236.004', 'Colecalciferol',                     'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Vitamina D3 2000UI',            '1.0244.0236.005', 'Colecalciferol',                     'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Vitamina B12 1000mcg',          '1.0244.0057.001', 'Cianocobalamina',                    'Sem Tarja',      True,  'Receita Simples',                           None),
    ('Cálcio + Vitamina D',           '1.0228.0047.003', 'Carbonato de Cálcio + Colecalciferol','Sem Tarja',     True,  'Receita Simples',                           None),
    ('Omeprazol 20mg (genérico)',     '1.0558.0380.004', 'Omeprazol',                          'Tarja Vermelha', True,  'Receita de Controle Especial (Branca)',      None),
]


def init_db(app):
    db.init_app(app)
    migrate.init_app(app, db)


def aplicar_migracoes_manuais(app):
    """Aplica colunas novas em tabelas existentes (seguro para SQLite e PostgreSQL)."""
    from sqlalchemy import text, inspect
    with app.app_context():
        with db.engine.connect() as conn:
            inspector = inspect(conn)
            _add_column_if_missing(conn, inspector, 'usuarios',               'ativo',           'BOOLEAN DEFAULT TRUE')
            _add_column_if_missing(conn, inspector, 'farmacias',              'razao_social',    'VARCHAR(200)')
            _add_column_if_missing(conn, inspector, 'receitas',               'status',          "VARCHAR(20) DEFAULT 'pendente'")
            _add_column_if_missing(conn, inspector, 'receitas',               'dispensada_em',   'TIMESTAMP')
            _add_column_if_missing(conn, inspector, 'receitas',               'dispensada_por_id','INTEGER')
            _add_column_if_missing(conn, inspector, 'receitas',               'tipo_receita',    'VARCHAR(60)')
            _add_column_if_missing(conn, inspector, 'receitas',               'imagem_url',      'VARCHAR(255)')
            _add_column_if_missing(conn, inspector, 'medicamentos',           'tarja',           "VARCHAR(30) DEFAULT 'Sem Tarja'")
            _add_column_if_missing(conn, inspector, 'medicamentos',           'principio_ativo', 'VARCHAR(120)')
            _add_column_if_missing(conn, inspector, 'medicamentos',           'uso_continuo',    'BOOLEAN DEFAULT FALSE')
            _add_column_if_missing(conn, inspector, 'medicamentos',           'referencia_id',   'INTEGER')
            _add_column_if_missing(conn, inspector, 'medicamentos_referencia','lista_portaria',  'VARCHAR(10)')
            conn.commit()


def seed_medicamentos_referencia(app):
    """Popula / atualiza a tabela de referência ANVISA (upsert por nome_comercial)."""
    from app.models.medicamento_referencia import MedicamentoReferencia
    with app.app_context():
        existentes = {r.nome_comercial for r in MedicamentoReferencia.query.all()}
        adicionados = 0
        for nome, reg, pa, tarja, continuo, tipo, lista in _REFERENCIA_ANVISA:
            if nome in existentes:
                continue
            ref = MedicamentoReferencia(
                nome_comercial=nome,
                registro_ms=reg,
                principio_ativo=pa,
                tarja=tarja,
                uso_continuo=continuo,
                tipo_receita=tipo,
                lista_portaria=lista,
            )
            db.session.add(ref)
            adicionados += 1
        if adicionados:
            db.session.commit()


def _add_column_if_missing(conn, inspector, table, column, col_type):
    from sqlalchemy import text
    tables = inspector.get_table_names()
    if table not in tables:
        return
    cols = [c['name'] for c in inspector.get_columns(table)]
    if column not in cols:
        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
