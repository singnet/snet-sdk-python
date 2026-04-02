from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PRIVATE_KEY: str = ""
    SIGNER_PRIVATE_KEY: str = ""
    ETH_RPC_ENDPOINT: str = ""
    WALLET_INDEX: int = 0
    IPFS_ENDPOINT: str = "/dns/ipfs.singularitynet.io/tcp/80/"
    CONCURRENCY: bool = True
    FORCE_UPDATE: bool = False
    MPE_CONTRACT_ADDRESS: str = ""
    REGISTRY_CONTRACT_ADDRESS: str = ""
    TOKEN_CONTRACT_ADDRESS: str = ""
    LIGHTHOUSE_TOKEN: str = " "

    model_config = SettingsConfigDict(
        env_prefix="SNET_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


config = Settings()


def configure(
    *,
    private_key: Optional[str] = None,
    signer_private_key: Optional[str] = None,
    eth_rpc_endpoint: Optional[str] = None,
    wallet_index: Optional[int] = None,
    ipfs_endpoint: Optional[str] = None,
    concurrency: Optional[bool] = None,
    force_update: Optional[bool] = None,
    mpe_contract_address: Optional[str] = None,
    registry_contract_address: Optional[str] = None,
    token_contract_address: Optional[str] = None,
    lighthouse_token: Optional[str] = None,
):
    global config
    for key, value in locals().items():
        key = key.upper()
        if hasattr(config, key):
            if value is not None:
                setattr(config, key, value)
        else:
            raise ValueError(f"Unknown config key: {key.lower()}")
