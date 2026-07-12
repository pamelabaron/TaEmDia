"""Service: regras de negócio dos clientes. Não conhece HTTP nem SQL diretamente."""
import uuid

from app.modules.clientes.models import Cliente
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import ClienteCreate, ClienteUpdate


class WhatsappDuplicadoError(Exception):
    """Já existe um cliente com esse número nesta conta (RF05/RN04/RN05)."""


class ClienteNaoEncontradoError(Exception):
    """Cliente inexistente ou de outro vendedor."""


class ClienteService:
    def __init__(self, repo: ClienteRepository):
        self.repo = repo

    def listar(self, vendedor_id: uuid.UUID) -> list[Cliente]:
        return self.repo.listar(vendedor_id)

    def cadastrar(self, vendedor_id: uuid.UUID, dados: ClienteCreate) -> Cliente:
        if self.repo.buscar_por_whatsapp(vendedor_id, dados.whatsapp_numero):
            raise WhatsappDuplicadoError()
        cliente = Cliente(
            vendedor_id=vendedor_id,
            nome=dados.nome,
            whatsapp_numero=dados.whatsapp_numero,
            cpf=dados.cpf,
            endereco=dados.endereco,
        )
        return self.repo.criar(cliente)

    def editar(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID, dados: ClienteUpdate) -> Cliente:
        cliente = self.repo.buscar_por_id(vendedor_id, cliente_id)
        if not cliente or not cliente.ativo:
            raise ClienteNaoEncontradoError()
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(cliente, campo, valor)
        return self.repo.salvar(cliente)

    def desativar(self, vendedor_id: uuid.UUID, cliente_id: uuid.UUID) -> None:
        """Soft delete: preserva o histórico (ver política de retenção do RFC)."""
        cliente = self.repo.buscar_por_id(vendedor_id, cliente_id)
        if not cliente:
            raise ClienteNaoEncontradoError()
        cliente.ativo = False
        self.repo.salvar(cliente)
