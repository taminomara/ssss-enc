#!/usr/bin/env python3

import argparse
import sys
import tempfile
import subprocess
import pyqrcode
import os
import shutil

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split secret into multiple parts using ssss-split, '
                    'generate a PDF with QR codes for each part')
    parser.add_argument(
        '-t', '--threshold', metavar='<n>', type=int,
        default=3,
        help='number of parts required to successfully recover the secret '
             '(default=3)')
    parser.add_argument(
        '-n', '--shares', metavar='<n>', type=int,
        default=5,
        help='total number of parts '
             '(default=5)')
    parser.add_argument(
        '-s', '--security', metavar='<n>', type=int,
        default=512,
        help='security level for ssss-split '
             '(default=512)')
    parser.add_argument(
        '-i', '--input', metavar='<file>', type=argparse.FileType('rb'),
        default=sys.stdin,
        help='where to read secret from '
             '(default=<stdin>)')
    parser.add_argument(
        '-o', '--output', metavar='<file>', type=argparse.FileType('wb'),
        default='secret.pdf',
        help='where to write the generated pdf '
             '(default=\'secret.pdf\')')

    args = parser.parse_args()

    text = args.input.read()

    if isinstance(text, str):
        text = text.encode()

    lines = subprocess.check_output(
        [
            'ssss-split',
            '-t', str(args.threshold),
            '-n', str(args.shares),
            '-s', str(args.security),
            '-q'
        ],
        input=text).decode().split()

    canvas = Canvas(args.output, pagesize=A4)

    top_padding = A4[1] - 2 * cm
    left_padding = 2 * cm
    font_size = 12
    line_size = 16
    width_chars = 41
    qr_size = 5 * cm

    for line in lines:
        canvas.setFont('Courier-Bold', font_size)
        canvas.drawString(left_padding, top_padding, "Important, do not discard")
        canvas.setFont('Courier', font_size)

        for l, i in enumerate(range(0, len(line), width_chars)):
            canvas.drawString(
                left_padding, top_padding - line_size * (l + 2),
                line[i:i + width_chars])

        dir = tempfile.mkdtemp()
        png = os.path.join(dir, 'qr.png')
        try:
            pyqrcode.create(line).png(png, scale=3, quiet_zone=0)
            canvas.drawImage(
                png,
                left_padding,
                top_padding - qr_size - line_size * (len(line) / width_chars + 3),
                qr_size, qr_size)
        finally:
            shutil.rmtree(dir)

        canvas.showPage()

    canvas.save()
