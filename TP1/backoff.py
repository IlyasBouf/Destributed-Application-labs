import time
import random
import urllib.request
import urllib.error
import json

# ── Fonction d'appel HTTP réelle (à implémenter) ──
def api_request(method, url, timeout=5, data=None, headers=None):
    """
    Effectue une requête HTTP et retourne (status_code, body).
    body peut être un dict (si JSON) ou une string.
    """
    try:
        # Préparer les headers par défaut
        req_headers = headers or {}
        
        # Préparer le body si nécessaire
        req_data = None
        if data is not None:
            if isinstance(data, dict):
                req_data = json.dumps(data).encode('utf-8')
                req_headers['Content-Type'] = 'application/json'
            else:
                req_data = data.encode('utf-8') if isinstance(data, str) else data
        
        # Créer et envoyer la requête
        req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            response_data = response.read().decode('utf-8')
            
            # Essayer de parser le JSON
            try:
                body = json.loads(response_data)
            except json.JSONDecodeError:
                body = response_data
            
            return status, body
            
    except urllib.error.HTTPError as e:
        # Erreur HTTP (4xx, 5xx)
        status = e.code
        try:
            body = json.loads(e.read().decode('utf-8'))
        except:
            body = str(e)
        return status, body
        
    except urllib.error.URLError as e:
        # Erreur réseau (connexion refusée, timeout, etc.)
        return None, {"error": "network_error", "message": str(e)}
        
    except Exception as e:
        # Autres erreurs
        return None, {"error": "unknown_error", "message": str(e)}


def request_with_retry(
    func,                       # fonction appelant l'API
    max_retries=4,              # nombre max de tentatives
    base_delay=1.0,             # délai initial (secondes)
    max_delay=30.0,             # délai maximum (plafond)
    retryable_statuses=(500, 502, 503, 504)
):
    """
    Appelle func() avec retry + backoff exponentiel + jitter.
    
    func() doit retourner (status_code, response_body).
    On ne retente QUE sur les codes de statut « retryables ».
    Les erreurs 4xx ne sont JAMAIS retentées (sauf 429).
    """
    
    for attempt in range(max_retries + 1):
        
        status, body = func()
        
        # ── Succès → retourner immédiatement ──
        if status is not None and status < 500 and status != 429:
            return status, body
        
        # ── Rate limited (429) → respecter Retry-After ──
        if status == 429:
            # En production, lire le header Retry-After
            wait = 30.0
            print(f"  ⏳ Rate limited. Attente {wait}s…")
            time.sleep(wait)
            continue
        
        # ── Dernière tentative atteinte → abandonner ──
        if attempt == max_retries:
            print(f"  💀 Abandon après {max_retries+1} tentatives")
            return status, body
        
        # ── Calculer le délai de backoff exponentiel ──
        delay = min(base_delay * (2 ** attempt), max_delay)
        
        # ── Ajouter du jitter (variation aléatoire) ──
        # "Full jitter" : valeur entre 0 et delay
        jittered_delay = random.uniform(0, delay)
        
        print(
            f"  🔄 Tentative {attempt+1}/{max_retries+1} "
            f"échouée (status={status}). "
            f"Retry dans {jittered_delay:.1f}s…"
        )
        time.sleep(jittered_delay)
    
    return status, body


# ── Exemple d'utilisation ──
if __name__ == "__main__":
    
    # On crée une closure pour passer les paramètres
    def call_health():
        return api_request("GET", 
                          "http://127.0.0.1:8080/health", 
                          timeout=5)
    
    status, body = request_with_retry(call_health)
    print(f"Résultat final : {status} → {body}")