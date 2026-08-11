from decimal import Decimal


def render_quote_appointment_client_email(price: Decimal, appointment_type: str) -> str:
    if appointment_type == "piercing":
        finisher = "Estamos ansiosos para brilharmos seu dia com um piercing incrivel! 🧜‍♀️🌊"
        appointment_name = "seu Piercing"
    else:
        finisher = "Estamos ansiosos para transformar sua ideia em uma tatuagem incrível! 🧜‍♀️🌊"
        appointment_name = "sua Tattoo"

    formatted_price = f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if formatted_price.endswith(",00"):
        formatted_price = formatted_price[:-3]

    formatted_price = f"R$ {formatted_price}"

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Seu orçamento está pronto!</title>
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
                ✨ Seu orçamento está pronto!
              </h2>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#444;font-size:15px;line-height:1.7;">

              <p>
                Oi! 🧜‍♀️💙
              </p>

              <p>
                Analisamos com carinho os detalhes do seu projeto e
                temos uma ótima notícia: já preparamos o seu orçamento!
              </p>

              <p>
                Para realizar {appointment_name} no
                <strong>Sereia Tattoo Studio</strong>, o investimento será de
                <strong>{formatted_price}</strong>.
              </p>

              <p>
                Ficamos muito felizes em poder fazer parte dessa ideia.
                Agora só falta alinhar os últimos
                detalhes e confirmar tudo para o seu atendimento. ✨
              </p>

              <p>
                Para reservar o seu horário, trabalhamos com um sinal de
                confirmação. Nossa equipe entrará em contato para explicar direitinho como
                funciona e tirar qualquer dúvida que você tiver.
              </p>

              <p>
                Se quiser conversar sobre o orçamento ou tiver qualquer
                dúvida sobre o seu projeto, é só entrar em contato conosco.
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
                Caso você não tenha solicitado este orçamento, basta
                desconsiderar esta mensagem.
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
