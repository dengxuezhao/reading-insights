from cryptography.fernet import Fernet
from backend.app.config import settings


def get_fernet() -> Fernet:
    """获取Fernet加密实例"""
    # 确保密钥长度为32字节，并进行base64编码
    key = settings.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
    # 将32字节密钥转换为Fernet可用的base64编码格式
    import base64
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_data(data: str) -> str:
    """加密数据"""
    if not data:
        return ""
    
    fernet = get_fernet()
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_data(encrypted_data: str) -> str:
    """解密数据"""
    if not encrypted_data:
        return ""
    
    try:
        fernet = get_fernet()
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        raise ValueError(f"解密失败: {str(e)}") 