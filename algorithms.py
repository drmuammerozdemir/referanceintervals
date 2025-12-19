import numpy as np
from scipy import stats

def run_hoffmann(data, use_log=True):
    # Hormon verileri genellikle log-normaldir
    working_data = np.log(data) if use_log else data
    sorted_data = np.sort(working_data)
    n = len(sorted_data)
    
    # Kümülatif olasılık (Hazen formülü)
    p = (np.arange(1, n + 1) - 0.5) / n
    z = stats.norm.ppf(p)
    
    # Lineer kısmın seçilmesi (Merkez %40-60 aralığı en sağlıklısıdır)
    mask = (p > 0.20) & (p < 0.80)
    slope, intercept, r, p_val, std_err = stats.linregress(z[mask], sorted_data[mask])
    
    # RI Hesaplama: Mean +/- 1.96 * SD
    low_z = intercept + (-1.96 * slope)
    high_z = intercept + (1.96 * slope)
    
    if use_log:
        return np.exp(low_z), np.exp(high_z), r
    return low_z, high_z, r
