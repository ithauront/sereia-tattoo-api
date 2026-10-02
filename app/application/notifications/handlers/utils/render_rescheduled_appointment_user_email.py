from datetime import datetime, timezone
from html import escape
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType


def render_rescheduled_appointment_artist_email(
    appointment_id: UUID,
    start_at: datetime,
    end_at: datetime,
    appointment_type: AppointmentType,
    was_deposit_retained: bool,
    has_confirmed_deposit: bool,
    client_email: str,
) -> str:
    client_email = escape(client_email)
    appointment_type_label = "Piercing" if appointment_type == AppointmentType.PIERCING else "Tattoo"

    start_at = start_at.astimezone(timezone.utc)
    end_at = end_at.astimezone(timezone.utc)
    formatted_date = start_at.strftime("%d/%m/%Y")
    formatted_start_time = start_at.strftime("%H:%M")
    formatted_end_time = end_at.strftime(
        "%H:%M" if start_at.date() == end_at.date() else "%d/%m/%Y %H:%M"
    )

    if was_deposit_retained:
        deposit_status = """
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:24px;background:#fff3f3;border:1px solid #e0a0a0;
                            border-radius:6px;">
                <tr>
                  <td style="padding:16px;color:#8a1c1c;font-size:15px;line-height:1.6;">
                    <strong>⚠️ CAUÇÃO RETIDA</strong>

                    <p style="margin:10px 0 0;">
                      A caução foi retida e não é válida para o horário reagendado.
                    </p>

                    <p style="margin:10px 0 0;">
                      <strong>Ação necessária:</strong> entre em contato com
                      o cliente para que ele realize o pagamento de uma nova
                      caução. O agendamento está aguardando uma nova caução
                      e precisa desse pagamento para ser confirmado novamente.
                    </p>
                  </td>
                </tr>
              </table>
        """
    elif has_confirmed_deposit:
        deposit_status = """
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:24px;background:#f3f8f3;border:1px solid #a8c5a8;
                            border-radius:6px;">
                <tr>
                  <td style="padding:16px;color:#285c28;font-size:15px;line-height:1.6;">
                    <strong>✓ CAUÇÃO MANTIDA</strong>

                    <p style="margin:10px 0 0;">
                      A caução permanece válida para o horário reagendado.
                    </p>
                  </td>
                </tr>
              </table>
        """

    else:
        deposit_status = """
              <p><strong>SEM CAUÇÃO CONFIRMADA</strong></p>
              <p>O reagendamento não confirmou uma caução. Consulte o status do
              agendamento e combine os próximos passos com o cliente.</p>
        """

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Agendamento reagendado</title>
</head>

<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">

  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <table width="100%" cellpadding="0" cellspacing="0"
               style="max-width:560px;background:#ffffff;border-radius:8px;padding:32px;">

          <tr>
            <td>
              <h2 style="margin:0;color:#222;">
                Agendamento remarcado
              </h2>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#444;font-size:15px;line-height:1.6;">

              <p>
                O agendamento foi remarcado. Confira os novos dados abaixo.
              </p>

              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-top:20px;border-collapse:collapse;">

                <tr>
                  <td style="padding:8px 0;color:#777;width:150px;">
                    <strong>ID do agendamento</strong>
                  </td>
                  <td style="padding:8px 0;">
                    {appointment_id}
                  </td>
                </tr>

                <tr>
                  <td style="padding:8px 0;color:#777;">
                    <strong>email do cliente</strong>
                  </td>
                  <td style="padding:8px 0;">
                    {client_email}
                  </td>
                </tr>

                <tr>
                  <td style="padding:8px 0;color:#777;">
                    <strong>Tipo</strong>
                  </td>
                  <td style="padding:8px 0;">
                    {appointment_type_label}
                  </td>
                </tr>

                <tr>
                  <td style="padding:8px 0;color:#777;">
                    <strong>Nova data</strong>
                  </td>
                  <td style="padding:8px 0;">
                    {formatted_date}
                  </td>
                </tr>

                <tr>
                  <td style="padding:8px 0;color:#777;">
                    <strong>Novo horário</strong>
                  </td>
                  <td style="padding:8px 0;">
                    {formatted_start_time} às {formatted_end_time} (UTC)
                  </td>
                </tr>

              </table>

              {deposit_status}

              <p style="margin-top:24px;">
                Consulte o agendamento pelo ID acima para verificar os
                demais detalhes e acompanhar o status.
              </p>

            </td>
          </tr>

          <tr>
            <td style="padding-top:28px;color:#999;font-size:12px;text-align:center;line-height:1.6;">
              <p style="margin:0;">
                Este é um e-mail enviado automaticamente pelo sistema do
                <strong>Sereia Tattoo Studio</strong>.
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
