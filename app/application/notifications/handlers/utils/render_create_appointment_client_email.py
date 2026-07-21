from datetime import datetime


def render_create_appointment_client_email(
    *, start_at: datetime, end_at: datetime, appointment_type: str
) -> str:
    if appointment_type == "piercing":
        title = "✨ Seu novo piercing está mais perto do que nunca!"
        appointment_name = "Piercing"
    else:
        title = "🎨 Sua próxima tattoo já começou a sair do papel!"
        appointment_name = "Tattoo"

    appointment_date = start_at.strftime("%d/%m/%Y")
    start_time = start_at.strftime("%H:%M")
    end_time = end_at.strftime("%H:%M")

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Solicitação de agendamento recebida</title>
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
                ✅ Solicitação recebida com sucesso!
              </h2>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#444;font-size:15px;line-height:1.7;">

              <p style="margin-top:0;">
                {title}
              </p>

              <p>
                Recebemos sua solicitação de agendamento no
                <strong>Sereia Tattoo Studio</strong>. ❤️🧜‍♀️
              </p>

              <p>
                Confira os dados enviados:
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
                Nossa equipe vai analisar sua solicitação e entrar em contato em breve
                para confirmar os detalhes, informar o valor final do procedimento e
                finalizar a reserva do seu horário.
              </p>

              <p>
                <strong>⚠️ Importante:</strong> este horário ainda depende da confirmação
                da nossa equipe. Assim que tudo estiver certo, entraremos em contato.
              </p>

              <p>
                Caso tenha informado algum dado incorretamente ou precise alterar a
                solicitação, entre em contato conosco o quanto antes. Teremos o maior
                prazer em ajudar. 😊
              </p>

              <p>
                Agradecemos por escolher o
                <strong>Sereia Tattoo Studio</strong>.
                Estamos ansiosos para receber você! 💙
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
                Se você não realizou esta solicitação, basta ignorar esta mensagem.
                Caso o agendamento não seja confirmado, ele será cancelado automaticamente.
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
