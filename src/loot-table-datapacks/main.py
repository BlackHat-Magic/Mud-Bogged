import argparse

def main():
    parser = argparse.ArgumentParser(description="Build tool for loot table tweak datapacks")

    parser.add_argument(
    	"datapack",
    	type=str,
    	help="Which datapack to build."
    )

    parser.add_argument(
    	"-v", "--version",
    	type=str,
    	default="26.2",
    	help="Which game version to build for."
    )

    parser.add_argument(
    	"-f", "--format",
    	type=int,
    	default=None,
    	help="Which datapack format to build (overrides game version)"
    )

    args = parser.parse_args()

    print(args.datapack)
    print(args.version)
    print(args.format)


if __name__ == "__main__":
    main()
