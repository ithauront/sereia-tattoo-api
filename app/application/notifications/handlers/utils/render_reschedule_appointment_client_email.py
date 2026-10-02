from datetime import datetime, timezone

from app.core.types.appointment_enums import AppointmentType


def render_rescheduled_appointment_client_email(
    start_at: datetime,
    end_at: datetime,
    was_deposit_retained: bool,
    has_confirmed_deposit: bool,
    appointment_type: AppointmentType,
) -> str:
    if appointment_type == AppointmentType.PIERCING:
        appointment_name = "seu Piercing"
        finisher = "Estamos ansiosos para deixar seu dia mais brilhante com um piercing incrível! 🧜‍♀️🌊"
    else:
        appointment_name = "sua Tattoo"
        finisher = "Estamos ansiosos para transformar sua ideia em uma tatuagem incrível! 🧜‍♀️🌊"

    start_at = start_at.astimezone(timezone.utc)
    end_at = end_at.astimezone(timezone.utc)
    formatted_date = start_at.strftime("%d/%m/%Y")
    formatted_start_time = start_at.strftime("%H:%M")
    formatted_end_time = end_at.strftime(
        "%H:%M" if start_at.date() == end_at.date() else "%d/%m/%Y %H:%M"
    )

    if was_deposit_retained:
        deposit_paragraph = """
              <p>
                A caução paga anteriormente foi retida pelo
                <strong>Sereia Tattoo Studio</strong>, conforme nossas regras de
                reagendamento, e não será utilizada para pagar este atendimento.
              </p>
              <p>
                Para confirmar o novo horário, será necessário pagar uma nova caução.
                Entre em contato com nossa equipe para combinar os detalhes.
              </p>
        """
    elif has_confirmed_deposit:
        deposit_paragraph = "<p>Sua caução permanece válida para o horário reagendado.</p>"
    else:
        deposit_paragraph = """
              <p>
                Este aviso informa a alteração de horário; ainda não há caução confirmada.
                Entre em contato com nossa equipe para combinar os próximos passos.
              </p>
        """

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Novo horário do seu atendimento</title>
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
                ✨ Novo horário do seu atendimento
              </h2>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#444;font-size:15px;line-height:1.7;">

              <p>
                Oi! 🧜‍♀️💙
              </p>

              <p>
                Temos uma atualização sobre o agendamento para
                <strong>{appointment_name}</strong> no
                <strong>Sereia Tattoo Studio</strong>.
              </p>

              <p>
                Seu atendimento foi reagendado para:
              </p>

              <p style="text-align:center;font-size:17px;">
                <strong>{formatted_date}</strong><br />
                <strong>{formatted_start_time} às {formatted_end_time} (UTC)</strong>
              </p>

              {deposit_paragraph}

              <p>
                Se tiver qualquer dúvida ou precisar de alguma informação
                sobre o reagendamento, é só entrar em contato conosco.
                Será um prazer ajudar! 😊
              </p>

              <p>
                <strong>Sereia Tattoo Studio</strong><br />
                {finisher}
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
                Caso você não tenha solicitado este reagendamento, entre em
                contato conosco para verificarmos a situação.
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
