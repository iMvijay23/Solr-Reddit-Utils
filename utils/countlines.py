
import zstandard
import json
import io

def count_json_objects(file_path):
    with open(file_path, 'rb') as fh:
        dctx = zstandard.ZstdDecompressor()
        stream_reader = dctx.stream_reader(fh)
        buffer = ""
        count = 0
        for chunk in io.TextIOWrapper(stream_reader, encoding='utf-8'):
            buffer += chunk
            try:
                while buffer:
                    json_object, idx = json.JSONDecoder().raw_decode(buffer)
                    buffer = buffer[idx:]
                    count += 1
            except ValueError:
                continue
        return count

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1]
    print(count_json_objects(file_path))
