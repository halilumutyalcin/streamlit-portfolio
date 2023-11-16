import pandas as pd
profiles = {
    'umut': {
        'AccessibleStocks': ['ISMEN', 'PETKM'],
        'Trades': pd.DataFrame({
            'Hisse': ['ISMEN', 'PETKM'],
            'Alım Tarihi': ['2023-01-01', '2023-02-01'],
            'Ort. Maliyet': [18, 25],
            'Adet': [100, 50],
        })
    },
    'hakan': {
        'AccessibleStocks': ['KERVN', 'THYAO'],
        'Trades': pd.DataFrame({
            'Hisse': ['KERVN', 'THYAO'],
            'Alım Tarihi': ['2023-03-01', '2023-04-01'],
            'Ort. Maliyet': [35, 45],
            'Adet': [75, 60],
        })
    }
}