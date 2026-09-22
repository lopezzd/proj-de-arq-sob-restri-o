import json
import base64

class KMS:
    """
    Key Management Service simulado.
    Gerencia as chaves de criptografia exclusivas por paciente.
    """
    def __init__(self):
        self.keys = {}
        self.counter = 1

    def generate_key_for_patient(self, patient_id: str) -> str:
        key = f"MOCK-KEY-SECURE-{self.counter}-{patient_id}"
        self.counter += 1
        self.keys[patient_id] = key
        return key

    def get_key(self, patient_id: str) -> str:
        return self.keys.get(patient_id)

    def delete_key(self, patient_id: str):
        if patient_id in self.keys:
            del self.keys[patient_id]

class EventStore:
    """
    Armazena os eventos do sistema de saúde de forma sequencial.
    Simula um banco de dados ou append-only log para event sourcing.
    """
    def __init__(self):
        self.events = []

    def append_event(self, event: dict):
        self.events.append(event)

    def get_all_events(self):
        return self.events

def mock_encrypt(data: str, key: str) -> str:
    if not key:
        raise ValueError("Chave invalida")
    encrypted_bytes = bytearray()
    key_bytes = key.encode('utf-8')
    for i, byte in enumerate(data.encode('utf-8')):
        encrypted_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def mock_decrypt(encrypted_data: str, key: str) -> str:
    if not key:
        raise ValueError("Chave invalida")
    encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
    key_bytes = key.encode('utf-8')
    decrypted_bytes = bytearray()
    for i, byte in enumerate(encrypted_bytes):
        decrypted_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
    return decrypted_bytes.decode('utf-8')

class HealthSystem:
    """
    Sistema central de saúde que gerencia eventos de pacientes.
    Integra-se com o KMS para criptografia de dados sensíveis visando 
    conformidade com a LGPD (Crypto-Shredding) e com o EventStore para persistência.
    """
    def __init__(self, kms: KMS, event_store: EventStore):
        self.kms = kms
        self.event_store = event_store
        self.event_counter = 1

    def register_patient_event(self, patient_id: str, event_type: str, public_data: dict, sensitive_data: dict):
        key = self.kms.get_key(patient_id)
        if not key:
            key = self.kms.generate_key_for_patient(patient_id)
        
        sensitive_json = json.dumps(sensitive_data, sort_keys=True)
        encrypted_payload = mock_encrypt(sensitive_json, key)
        
        event = {
            "event_id": f"EVT-{self.event_counter:04d}",
            "patient_id": patient_id,
            "event_type": event_type,
            "public_data": public_data,
            "sensitive_payload": encrypted_payload
        }
        self.event_counter += 1
        self.event_store.append_event(event)

    def read_patient_events(self, patient_id: str):
        key = self.kms.get_key(patient_id)
        patient_events = [e for e in self.event_store.get_all_events() if e["patient_id"] == patient_id]
        
        results = []
        for e in patient_events:
            event_copy = dict(e)
            if key:
                try:
                    decrypted_json = mock_decrypt(e["sensitive_payload"], key)
                    event_copy["sensitive_payload_decrypted"] = json.loads(decrypted_json)
                except Exception:
                    event_copy["sensitive_payload_decrypted"] = "ERRO_DECRIPTOGRAFIA"
            else:
                event_copy["sensitive_payload_decrypted"] = "DADOS_ESQUECIDOS_LGPD"
            results.append(event_copy)
        return results

def run_spike():
    kms = KMS()
    store = EventStore()
    sys = HealthSystem(kms, store)

    patient_1 = "PAC-001"
    
    sys.register_patient_event(
        patient_1,
        "RemedioDispensadoEvent",
        {"remedio": "Losartana", "quantidade": 2, "unidade": "UBS Centro", "data": "2024-05-10"},
        {"cpf": "111.222.333-44", "diagnostico": "Hipertensao", "nome": "Joao da Silva"}
    )
    
    sys.register_patient_event(
        patient_1,
        "AtendimentoRealizadoEvent",
        {"data": "2024-06-15", "medico_crm": "CRM-1234", "tipo": "Consulta"},
        {"nome": "Joao da Silva", "pressao": "15/9", "sintomas": "Dor de cabeca constante"}
    )

    print("--- LENDO EVENTOS COM A CHAVE ATIVA (Cenario Normal) ---")
    events = sys.read_patient_events(patient_1)
    for ev in events:
        print(f"Evento ID: {ev['event_id']} | Tipo: {ev['event_type']}")
        print(f"Dados Publicos (Auditoria): {ev['public_data']}")
        print(f"Dados Sensiveis Abertos: {ev.get('sensitive_payload_decrypted')}")
        print(f"Payload Criptografado no Banco: {ev['sensitive_payload']}")
        print("-" * 60)

    print("\n--- PACIENTE SOLICITA ESQUECIMENTO (LGPD) ---")
    print("Destruindo chave no KMS...")
    kms.delete_key(patient_1)
    print("Chave destruida com sucesso!\n")

    print("--- LENDO EVENTOS APOS CRYPTO-SHREDDING ---")
    events_after = sys.read_patient_events(patient_1)
    for ev in events_after:
        print(f"Evento ID: {ev['event_id']} | Tipo: {ev['event_type']}")
        print(f"Dados Publicos (Auditoria Intacta): {ev['public_data']}")
        print(f"Dados Sensiveis: {ev.get('sensitive_payload_decrypted')}")
        print(f"Payload Criptografado no Banco: {ev['sensitive_payload']}")
        print("-" * 60)

if __name__ == "__main__":
    run_spike()
