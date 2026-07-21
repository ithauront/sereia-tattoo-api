from datetime import datetime


def render_create_appointment_user_email(
    *, start_at: datetime, end_at: datetime, appointment_type: str
) -> str:
    appointment_name = "Piercing" if appointment_type == "piercing" else "Tattoo"

    appointment_date = start_at.strftime("%d/%m/%Y")
    start_time = start_at.strftime("%H:%M")
    end_time = end_at.strftime("%H:%M")

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Nova solicitação de agendamento</title>
</head>

<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <table width="100%" cellpadding="0" cellspacing="0"
               style="max-width:520px;background:#ffffff;border-radius:8px;padding:32px;">

          <tr>
            <td align="center">
              <h2 style="margin:0;color:#222;">
                📅 Nova solicitação de agendamento
              </h2>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#444;font-size:15px;line-height:1.7;">

              <p style="margin-top:0;">
                Sua agenda no <strong>Sereia Tattoo Studio</strong> recebeu uma nova solicitação. 🎉
              </p>

              <p>
                Confira os detalhes abaixo:
              </p>

              <div style="background:#f8f8f8;border-radius:6px;padding:16px;margin:20px 0;">
                <p style="margin:0 0 8px 0;">
                  <strong>Procedimento:</strong> {appointment_name}
                </p>

                <p style="margin:0 0 8px 0;">
                  <strong>Data:</strong> {appointment_date}
                </p>

                <p style="margin:0;">
                  <strong>Horário:</strong> {start_time} às {end_time}
                </p>
              </div>

              <p>
                Agora basta acessar o sistema para revisar a solicitação,
                informar o valor do procedimento e entrar em contato com o cliente
                para prosseguir com a confirmação do agendamento e o pagamento da caução.
              </p>

              <p>
                Quanto mais rápido o atendimento, maior a chance de converter essa
                solicitação em um agendamento confirmado. 🚀
              </p>

              <p>
                Caso encontre qualquer problema para visualizar a solicitação,
                entre em contato com o suporte para que possamos ajudar.
              </p>

            </td>
          </tr>

          <tr>
            <td style="padding-top:28px;color:#999;font-size:12px;text-align:center;line-height:1.6;">

              <p style="margin:0;">
                Este é um e-mail enviado automaticamente pelo sistema do
                <strong>Sereia Tattoo Studio</strong>.
              </p>

              <p style="margin-top:12px;">
                Caso precise de ajuda, nossa equipe de suporte estará à disposição.
              </p>

            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>
</body>
</html>
""".strip()
