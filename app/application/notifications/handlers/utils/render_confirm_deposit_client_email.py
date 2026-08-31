from datetime import datetime
from decimal import Decimal


def render_confirm_deposit_client_email(
    *,
    amount: Decimal,
    appointment_type: str,
    start_at: datetime,
) -> str:
    if appointment_type == "piercing":
        appointment_name = "seu piercing ✨"
        tattoo_preparation_tip = ""
    elif appointment_type == "tattoo":
        appointment_name = "sua tattoo 🎨"
        tattoo_preparation_tip = """
          <p style="margin:14px 0 0;color:#666;font-size:14px;line-height:1.6;">
            • Se a região escolhida para a tatuagem estiver ressecada, você
            pode aplicar hidratante nos dias que antecedem o procedimento,
            mantendo a pele bem cuidada e hidratada.
          </p>
        """
    else:
        raise ValueError(f"Unknown appointment type: {appointment_type}")

    appointment_date = start_at.strftime("%d/%m/%Y")
    start_time = start_at.strftime("%H:%M")

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agendamento confirmado</title>
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
                Agendamento confirmado! ✨
              </h1>

              <p
                style="
                  margin:12px 0 0;
                  color:#777;
                  font-size:15px;
                "
              >
                Seu horário está reservado com carinho. 💙
              </p>
            </td>
          </tr>

          <!-- Confirmation -->
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
                Recebemos seu pagamento de
                <strong>R$ {amount:.2f}</strong> e está tudo certo com o
                seu agendamento. Estamos muito felizes em receber você para
                fazer {appointment_name}, no dia <strong>{appointment_date}</strong>,
                às <strong>{start_time}</strong>, no
                 <strong>Sereia Tattoo Studio</strong>. 🧜‍♀️💙
              </p>

              
            </td>
          </tr>

          <!-- Important information -->
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
                      <strong>Algumas informações importantes 💙</strong>
                    </p>

                    <p
                      style="
                        margin:0 0 10px;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      Para que tudo corra da melhor forma, deixamos aqui
                      algumas informações importantes sobre o nosso
                      agendamento:
                    </p>

                    <p
                      style="
                        margin:0 0 10px;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      • O valor da caução será descontado do valor final
                      do procedimento.
                    </p>

                    <p
                      style="
                        margin:0 0 10px;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      • Caso precise cancelar ou remarcar, pedimos que nos
                      avise com pelo menos
                      <strong>72 horas de antecedência</strong>.
                      Dessa forma, conseguimos reorganizar nossa agenda e
                      preservar o valor da caução.
                    </p>

                    <p
                      style="
                        margin:0 0 18px;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      • Em caso de ausência ou atraso superior a
                      <strong>30 minutos</strong>, a caução poderá ser perdida.
                    </p>

                    <!-- Preparation tips -->
                    <p
                      style="
                        margin:20px 0 12px;
                        color:#333;
                        font-size:15px;
                      "
                    >
                      <strong>Uma dica para o seu procedimento ✨</strong>
                    </p>

                    <p
                      style="
                        margin:0 0 10px;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      Nos dias que antecedem o seu horário, procure manter-se
                      bem hidratado(a) e fazer suas refeições normalmente.
                      Se possível, evite refeições muito pesadas ou
                      excessivamente gordurosas antes do procedimento.
                    </p>

                    {tattoo_preparation_tip}

                    <p
                      style="
                        margin:14px 0 0;
                        color:#666;
                        font-size:14px;
                        line-height:1.6;
                      "
                    >
                      Essas são apenas recomendações para que você chegue
                      ao estúdio se sentindo bem e preparado(a). 😊
                    </p>

                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Contact -->
          <tr>
            <td
              style="
                padding:28px 32px 0;
                color:#444;
                font-size:15px;
                line-height:1.7;
              "
            >
              <p style="margin:0;">
                Se precisar corrigir alguma informação ou tiver qualquer
                dúvida antes do seu horário, é só entrar em contato conosco.
                Teremos prazer em ajudar! 😊
              </p>
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
                Obrigado por escolher o
                <strong>Sereia Tattoo Studio</strong>.
              </p>

              <p style="margin:8px 0 0;">
                Estamos ansiosos para receber você! 💙🧜‍♀️
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
                Se você não realizou esta solicitação, basta ignorar esta
                mensagem.
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
