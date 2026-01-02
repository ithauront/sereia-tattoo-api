def render_activation_email(activation_link: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Ative sua conta</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:6px;padding:32px;">
          
          <tr>
            <td style="text-align:center;">
              <h2 style="margin-bottom:16px;color:#222;">
                Ative sua conta
              </h2>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;">
              <p>
                Você foi convidado para criar uma conta no <strong>Sereia Tattoo</strong>.
              </p>

              <p>
                Para ativar sua conta e definir sua senha, clique no botão abaixo:
              </p>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding:24px 0;">
              <a href="{activation_link}"
                 style="
                   background:#111;
                   color:#ffffff;
                   padding:12px 20px;
                   text-decoration:none;
                   border-radius:4px;
                   font-size:14px;
                   display:inline-block;
                 ">
                Ativar minha conta
              </a>
            </td>
          </tr>

          <tr>
            <td style="color:#666;font-size:12px;line-height:1.5;">
              <p>
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </p>

              <p style="word-break:break-all;">
                <a href="{activation_link}" style="color:#555;">
                  {activation_link}
                </a>
              </p>

              <p>
                Este link é válido por um tempo limitado a 15 minutos.
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
