import time
import random
import urllib.request
import urllib.error

def simple_api_request(url, timeout=5):
    """Version ultra simple pour tester."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.getcode(), response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except urllib.error.URLError as e:
        return None, str(e)

def request_with_retry_simple(url, max_retries=4, base_delay=1.0):
    """Version simplifiée qui prend directement l'URL."""
    for attempt in range(max_retries + 1):
        status, body = simple_api_request(url)
        
        if status is not None and status < 500:
            return status, body
        
        if attempt == max_retries:
            print(f"Abandon après {max_retries+1} tentatives")
            return status, body
        
        delay = min(base_delay * (2 ** attempt), 30.0)
        jittered = random.uniform(0, delay)
        print(f"Tentative {attempt+1} échouée (status={status}), retry dans {jittered:.1f}s")
        time.sleep(jittered)
    
    return status, body

# Test
if __name__ == "__main__":
    status, body = request_with_retry_simple("http://127.0.0.1:8080/health")
    print(f"Résultat : {status} → {body}")