import click
import configparser
import emails
from datetime import datetime
from lib.nbrun import run_notebook
from pathlib import Path


def send_email(notebook, out_path, config, is_error=False):
    if 'email' not in config.sections() or not config.get('email', 'recipient'):
        print('Not sending email, config is not set')
        return
    email = config.get('email', 'recipient')
    message = 'Notebook output is attached.'
    subject = '%s for notebook %s' % ('ERROR' if is_error else 'SUCCESS', notebook)
    message = emails.html(html='<p>%s</p>' % message,
                          subject=subject,
                          mail_from=email)
    filename = '%s.html' % out_path
    message.attach(data=open(filename, 'rb'), filename=filename)
    smtp = {'host': 'smtp.mailjet.com', 'port': 465, 'ssl': True,
            'user': config.get('email', 'smtp_user'),
            'password': config.get('email', 'smtp_password')}
    message.send(to=email, smtp=smtp)


@click.command()
@click.argument('notebook_file')
@click.option('--settings', default='config.ini', help='Config file')
def execute(notebook_file, settings):
    if not Path(settings).exists():
        print('No config file %s' % settings)
        return

    config = configparser.ConfigParser()
    config.read(settings)

    output_folder = config.get('general', 'output_folder')
    suffix = datetime.now().strftime('%Y%m%d-%H%M%S')
    notebook_name = notebook_file.split('/')[-1].replace('.ipynb', '')
    out_filename = '%s_%s' % (notebook_name, suffix)
    out_path = Path(output_folder) / notebook_name
    out_path.mkdir(parents=True, exist_ok=True)
    out_path = out_path / out_filename

    is_error = False
    try:
        run_notebook(notebook_file, save_html=True, suffix=suffix,
                     out_path_ipynb='%s.ipynb' % out_path,
                     out_path_html='%s.html' % out_path)
    except Exception as e: # noqa
        print(e)
        is_error = True
    finally:
        send_email(notebook_name, out_path, config, is_error=is_error)


if __name__ == '__main__':
    execute()