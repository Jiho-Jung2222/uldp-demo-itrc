import numpy as np
from scipy.optimize import minimize_scalar, minimize

def compute_M_J(alpha, t, w, v, epsilon):
    """compute_M_J.m의 파이썬 구현"""
    expEps = np.exp(epsilon)
    k = np.arange(1, v + 1)
    
    if alpha >= 1.0 - 1e-9:
        J2, J3 = np.inf, np.inf
    else:
        J2 = ((w - v) * (expEps - 1) / (1 - alpha)) * np.sum(t * k / (k * expEps + v - k))
        J3 = (v * (w - v) * (expEps - 1) / (w * (1 - alpha))) * np.sum(t * k / (alpha * k * (expEps - 1) + v))
        
    if v > 1:
        denom = (alpha * k * (expEps - 1) + v) * (k * expEps + v - k)
        J1 = (v * (expEps - 1)**2) / (v - 1) * np.sum(t * (k * (v - k)) / denom)
    else:
        J1 = np.inf

    M1 = (v - 1) / J1 if J1 > 0 else np.inf
    M2 = (w - v - 1) / J2 if J2 > 0 else np.inf
    M3 = 1 / J3 if J3 > 0 else np.inf
    
    return M1 + M2 + M3, J1, J2, J3

def optimize_M(w, v, epsilon):
    """optimize_M.m의 파이썬 구현 (SLSQP 및 bounded 최적화 사용)"""
    def inner_min_t(alpha):
        t0 = np.ones(v) / v
        bounds = [(0, 1) for _ in range(v)]
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        res = minimize(lambda x: compute_M_J(alpha, x, w, v, epsilon)[0], t0, method='SLSQP', bounds=bounds, constraints=constraints)
        return res.fun, res.x

    res_alpha = minimize_scalar(lambda a: -inner_min_t(a)[0], bounds=(0, 1), method='bounded')
    alpha_opt = res_alpha.x
    M_val, t_opt = inner_min_t(alpha_opt)
    
    t_opt[t_opt < 1e-8] = 0
    t_opt = t_opt / np.sum(t_opt)
    return alpha_opt, t_opt

def encodeSensUsers(rawData_sens, k, randFlagSens, v, epsilon):
    """encode_opt_ULDP.m 내 encodeSensUsers 함수의 벡터화 구현"""
    numSens = len(rawData_sens)
    expEps = np.exp(epsilon)
    
    pInclSens = expEps / (expEps + v/k - 1)
    inclSens = randFlagSens < pInclSens
    
    randMatSens = np.random.rand(numSens, v)
    linIdx = np.arange(numSens)
    randMatSens[linIdx, rawData_sens] = np.inf
    randMatSens[linIdx[inclSens], rawData_sens[inclSens]] = -np.inf
    
    # MATLAB의 mink 대체 (가장 작은 k개의 인덱스 추출)
    colsSens = np.argpartition(randMatSens, k - 1, axis=1)[:, :k]
    
    Y_P = np.zeros((numSens, v), dtype=bool)
    row_idx = np.repeat(np.arange(numSens), k)
    Y_P[row_idx, colsSens.flatten()] = True
    return Y_P

def encode_opt_ULDP(rawData, opt_alpha, opt_t, w, v, epsilon):
    """encode_opt_ULDP.m의 파이썬 벡터화 구현"""
    n = len(rawData)
    expEps = np.exp(epsilon)
    Y = np.zeros((n, w), dtype=bool)
    
    isSens = rawData < v
    idxSens = np.where(isSens)[0]
    idxNon = np.where(~isSens)[0]
    
    randFlag = np.random.rand(n)
    randFlagSens = randFlag[idxSens]
    randFlagNon = randFlag[idxNon]
    
    k_arr = np.where(opt_t > 0)[0] + 1
    mix = len(k_arr) >= 2
    
    if not mix:
        k = k_arr[0]
        Y[idxSens, :v] = encodeSensUsers(rawData[idxSens], k, randFlagSens, v, epsilon)
        
        pInclNon = (expEps - 1) / (expEps + v/k - 1)
        inclNon = randFlagNon < pInclNon
        Y[idxNon[inclNon], rawData[idxNon[inclNon]]] = True
        
        idxExclNon = idxNon[~inclNon]
        if len(idxExclNon) > 0:
            randMatNon = np.random.rand(len(idxExclNon), v)
            colsNon = np.argpartition(randMatNon, k - 1, axis=1)[:, :k]
            row_idx = np.repeat(idxExclNon, k)
            Y[row_idx, colsNon.flatten()] = True
    else:
        cdf_t = np.cumsum(opt_t)
        k_Sens = np.digitize(randFlagSens, np.concatenate([[0], cdf_t]))
        
        for kk in k_arr:
            rel = k_Sens == kk
            if np.any(rel):
                Y[idxSens[rel], :v] = encodeSensUsers(rawData[idxSens][rel], kk, randFlagSens[rel], v, epsilon)
        
        pNon2Y_P = opt_t * (v / (np.arange(1, v+1) * expEps + v - np.arange(1, v+1)))
        pInclNon = 1 - np.sum(pNon2Y_P)
        probVec = np.concatenate([pNon2Y_P, [pInclNon]])
        choice = np.digitize(randFlagNon, np.concatenate([[0], np.cumsum(probVec)]))
        
        idMask = choice == len(probVec)
        Y[idxNon[idMask], rawData[idxNon][idMask]] = True
        
        for kk in k_arr:
            rel = choice == kk
            absIdx = idxNon[rel]
            if len(absIdx) > 0:
                randFlag_k = np.random.rand(len(absIdx), v)
                cols = np.argpartition(randFlag_k, kk - 1, axis=1)[:, :kk]
                row_idx = np.repeat(absIdx, kk)
                Y[row_idx, cols.flatten()] = True
                
    return Y

def project2H(hvec, v, w):
    """decode_opt_ULDP.m 내 project2H의 파이썬 구현"""
    m1 = np.mean(hvec[:v])
    proj1 = np.concatenate([hvec[:v] - m1, np.zeros(w - v)])
    m2 = np.mean(hvec[v:])
    proj2 = np.concatenate([np.zeros(v), hvec[v:] - m2])
    u = np.concatenate([(w - v) * np.ones(v), -v * np.ones(w - v)])
    proj3 = (np.dot(u, hvec) / np.dot(u, u)) * u
    return proj1, proj2, proj3

def decode_opt_ULDP(Y, opt_alpha, opt_t, w, v, epsilon):
    """decode_opt_ULDP.m의 파이썬 구현 (단일 및 혼합 모드 지원)"""
    n = Y.shape[0]
    expEps = np.exp(epsilon)
    k_arr = np.where(opt_t > 0)[0] + 1
    
    if len(k_arr) == 1:
        k = k_arr[0]
        freq = np.sum(Y, axis=0) / n
        coeff1 = (expEps - 1) / (expEps + v / k - 1)
        coeff2 = coeff1 * (v - k) / (v - 1)
        coeff3 = ((k - 1) * expEps + v - k) / ((v - k) * (expEps - 1))
        
        p_hat = np.zeros(w)
        freq_nonSet_sum = np.sum(freq[v:])
        p_hat[:v] = (freq[:v] + (k - 1) * freq_nonSet_sum / (v - 1)) / coeff2 - coeff3
        p_hat[v:] = freq[v:] / coeff1
    else:
        P_alpha = np.zeros(w)
        P_alpha[:v] = opt_alpha / v
        P_alpha[v:] = (1 - opt_alpha) / (w - v)
        
        _, J1, J2, J3 = compute_M_J(opt_alpha, opt_t, w, v, epsilon)
        
        Y_P = Y[:, :v]
        Y_I = Y[:, v:]
        eta = np.zeros(w)
        
        subsetSizes = np.sum(Y_P, axis=1)
        isMixtureRow = np.isin(subsetSizes, k_arr)
        
        for i in np.where(isMixtureRow)[0]:
            Q_x = np.ones(w)
            Q_x[:v][Y_P[i, :]] = expEps
            eta += Q_x / np.sum(P_alpha * Q_x) / n
            
        valid = np.sum(Y_I, axis=1) == 1
        freq = np.sum(Y_I[valid], axis=0) / n
        eta_I = np.zeros(w)
        eta_I[v:] = freq * (w - v) / (1 - opt_alpha)
        eta += eta_I
        
        Phi1, Phi2, Phi3 = project2H(eta, v, w)
        p_hat = P_alpha + (Phi1 / J1 + Phi2 / J2 + Phi3 / J3)
        
    p_hat = np.maximum(p_hat, 0)
    return p_hat / np.sum(p_hat)