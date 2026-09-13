from datetime import datetime


def render_appointment_cancellation_client_email(
    *,
    start_at: datetime,
    end_at: datetime,
    appointment_type: str,
    has_confirmed_deposit: bool,
    is_eligible_for_deposit_refund: bool,
) -> str:

    if appointment_type == "piercing":
        appointment_name = "seu piercing ✨"
    elif appointment_type == "tattoo":
        appointment_name = "sua tattoo 🎨"
    else:
        raise ValueError(f"Unknown appointment type: {appointment_type}")

    appointment_date = start_at.strftime("%d/%m/%Y")
    start_time = start_at.strftime("%H:%M")
    end_time = end_at.strftime("%H:%M")

    if not has_confirmed_deposit or is_eligible_for_deposit_refund:
        deposit_refund_message = ""
    else:
        deposit_refund_message = """
      <p
        style="
          margin:18px 0 0;
          color:#666;
          font-size:14px;
          line-height:1.6;
        "
      >
        De acordo com as regras da empresa, este cancelamento foi feito
        de uma forma que <strong>não permite o reembolso de uma possível
        caução</strong> referente ao agendamento.
      </p>
    """

    return f"""

<!DOCTYPE html>

<html lang="pt-BR">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agendamento cancelado</title>
</head>

<body
  style="
    margin:0;
    padding:0;
    background-color:#f5f5f5;
    font-family:Arial,Helvetica,sans-serif;
    color:#333;
  "
>
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding:40px 16px;">

    <table
      width="100%"
      cellpadding="0"
      cellspacing="0"
      border="0"
      style="
        max-width:560px;
        background:#ffffff;
        border-radius:10px;
        overflow:hidden;
      "
    >

      <!-- Header -->
      <tr>
        <td
          align="center"
          style="padding:36px 32px 28px;background:#ffffff;"
        >
          <h1
            style="
              margin:0;
              color:#222;
              font-size:24px;
              font-weight:600;
            "
          >
            Agendamento cancelado 💙
          </h1>

          <p
            style="
              margin:12px 0 0;
              color:#777;
              font-size:15px;
            "
          >
            Tudo bem! Esperamos receber você em uma próxima oportunidade. ✨
          </p>
        </td>
      </tr>

      <!-- Cancellation -->
      <tr>
        <td
          style="
            padding:28px 32px 0;
            color:#444;
            font-size:15px;
            line-height:1.7;
          "
        >
          <p style="margin:0 0 18px;">
            Seu agendamento para
            <strong>{appointment_name}</strong> foi cancelado e o horário
            reservado para o dia
            <strong>{appointment_date}</strong>, das
            <strong>{start_time}</strong> às
            <strong>{end_time}</strong>, não está mais reservado para você.
          </p>

          <p style="margin:0;">
            Sabemos que imprevistos acontecem, então não se preocupe. 😊
            Quando você quiser marcar novamente, será um prazer
            receber você no
            <strong>Sereia Tattoo Studio</strong>. 🧜‍♀️💙
          </p>

          {deposit_refund_message}

        </td>
      </tr>

      <!-- Appointment information -->
      <tr>
        <td style="padding:28px 32px 0;">

          <table
            width="100%"
            cellpadding="0"
            cellspacing="0"
            border="0"
            style="border-top:1px solid #eeeeee;"
          >
            <tr>
              <td style="padding-top:24px;">

                <p
                  style="
                    margin:0 0 12px;
                    color:#333;
                    font-size:15px;
                  "
                >
                  <strong>Informações do agendamento</strong>
                </p>

                <p
                  style="
                    margin:0 0 10px;
                    color:#666;
                    font-size:14px;
                    line-height:1.6;
                  "
                >
                  • Procedimento: <strong>{appointment_name}</strong>
                </p>

                <p
                  style="
                    margin:0 0 10px;
                    color:#666;
                    font-size:14px;
                    line-height:1.6;
                  "
                >
                  • Data: <strong>{appointment_date}</strong>
                </p>

                <p
                  style="
                    margin:0;
                    color:#666;
                    font-size:14px;
                    line-height:1.6;
                  "
                >
                  • Horário: <strong>{start_time} – {end_time}</strong>
                </p>

              </td>
            </tr>
          </table>

        </td>
      </tr>

      <!-- New appointment -->
      <tr>
        <td
          style="
            padding:28px 32px 0;
            color:#444;
            font-size:15px;
            line-height:1.7;
          "
        >
          <table
            width="100%"
            cellpadding="0"
            cellspacing="0"
            border="0"
            style="
              border-top:1px solid #eeeeee;
            "
          >
            <tr>
              <td
                align="center"
                style="padding-top:24px;"
              >

                <p
                  style="
                    margin:0 0 10px;
                    color:#333;
                    font-size:16px;
                  "
                >
                  <strong>Que tal escolher um novo horário? ✨</strong>
                </p>

                <p
                  style="
                    margin:0;
                    color:#666;
                    font-size:14px;
                    line-height:1.6;
                  "
                >
                  Se ainda quiser fazer
                  <strong>{appointment_name}</strong>,
                  entre em contato conosco e vamos encontrar um novo
                  horário que funcione para você. 💙
                </p>

              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Closing -->
      <tr>
        <td
          align="center"
          style="
            padding:28px 32px 0;
            color:#444;
            font-size:15px;
            line-height:1.7;
          "
        >
          <p style="margin:0;">
            Vamos ficar felizes em ter você de volta! 🥰
          </p>

          <p style="margin:8px 0 0;">
            Até a próxima! ✨🧜‍♀️
          </p>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td
          align="center"
          style="
            padding:28px 32px 32px;
            color:#aaa;
            font-size:12px;
            line-height:1.6;
          "
        >
          <p style="margin:0;">
            Este é um e-mail enviado automaticamente pelo sistema do
            <strong>Sereia Tattoo Studio</strong>.
          </p>

          <p style="margin:12px 0 0;">
            Se você tiver alguma dúvida, entre em contato conosco.
            Estamos sempre à disposição para ajudar. 💙
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
