from datetime import date


def render_booking_window_email(new_booking_window: date) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Novas datas foram abertas na agenda</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:6px;padding:32px;">
          
          <tr>
            <td style="text-align:center;">
              <h2 style="margin-bottom:16px;color:#222;">
                Novas datas estão disponiveis para agendamento com você!
              </h2>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;">
              <p>
                Por favor verifique as datas abertas.
              </p>

              <p>
               A agenda esta aberta e disponivel até <strong>{new_booking_window}</strong>
              </p>
            </td>
          </tr>

          <tr>
            <td style="color:#666;font-size:12px;line-height:1.5;">
              <p>
                Caso essas datas correspondam a o que você esperava nenhuma ação precisa ser feita.
              </p>

        
              <p>
                <strong>Caso não concorde com a disponibilidade até {new_booking_window}, 
                atualize as datas disponiveis pelo nosso sistema.</strong>
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#999;font-size:11px;text-align:center;">
              <p>
                Se você não esperava este email, pode ignorá-lo com segurança.
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
