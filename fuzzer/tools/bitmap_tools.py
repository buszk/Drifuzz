import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bitmap', type=str)
    parser.add_argument('--virgin', default=False, action='store_true')
    args = parser.parse_args()
    bitmap = bytearray()
    covered_bytes = 0
    fully_covered_bytes = 0
    with open(args.bitmap, 'rb') as f:
        bitmap = f.read()
    for i in range(len(bitmap)):
        if args.virgin:
            covered = bitmap[i]
        else:
            covered = 255 - bitmap[i]
        if covered:
            covered_bytes += 1
            if covered == 255:
                fully_covered_bytes += 1
    print('Bitmap %s' % args.bitmap)
    print('    covers %d bytes in which %d are fully covered' % (covered_bytes, fully_covered_bytes))


if __name__ == '__main__':
    main()