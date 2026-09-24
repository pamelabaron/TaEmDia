/**
 * A recusa por assinatura vencida (402) já é explicada pelo diálogo que o
 * interceptor abre. As telas devem parar antes do próprio aviso genérico:
 * senão a pessoa lê "Erro ao cadastrar cliente", que não é o que aconteceu.
 *
 * Use depois de desligar os indicadores de "salvando", nunca antes: quem é
 * bloqueado também precisa ter o botão devolvido.
 */
export function bloqueadoPorAssinatura(erro: unknown): boolean {
  return (erro as { status?: number })?.status === 402;
}
