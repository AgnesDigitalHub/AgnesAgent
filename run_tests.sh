#!/bin/bash

# AgnesAgent 测试运行脚本
# 使用方法: ./run_tests.sh [选项]

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "AgnesAgent 测试运行脚本"
    echo ""
    echo "使用方法:"
    echo "  ./run_tests.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -a, --all               运行所有测试"
    echo "  -u, --unit              只运行单元测试"
    echo "  -i, --integration       只运行集成测试"
    echo "  -s, --slow              包含慢速测试"
    echo "  -c, --coverage          生成覆盖率报告"
    echo "  -v, --verbose           详细输出"
    echo "  -f, --file FILE         运行指定测试文件"
    echo "  -k, --keyword KEYWORD   运行包含关键词的测试"
    echo "  -m, --module MODULE     运行指定模块的测试 (core|skills|mcp|web2|utils)"
    echo "  -r, --report            生成HTML测试报告"
    echo "  --clean                 清理测试缓存和报告"
    echo ""
    echo "示例:"
    echo "  ./run_tests.sh -a -c          # 运行所有测试并生成覆盖率报告"
    echo "  ./run_tests.sh -m core        # 只运行core模块测试"
    echo "  ./run_tests.sh -f tests/test_llm.py  # 运行指定测试文件"
    echo "  ./run_tests.sh -k 'test_chat' # 运行包含'test_chat'的测试"
    echo "  ./run_tests.sh -r             # 生成HTML测试报告"
}

# 默认参数
RUN_ALL=false
RUN_UNIT=false
RUN_INTEGRATION=false
INCLUDE_SLOW=false
COVERAGE=false
VERBOSE=false
FILE=""
KEYWORD=""
MODULE=""
REPORT=false
CLEAN=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -u|--unit)
            RUN_UNIT=true
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=true
            shift
            ;;
        -s|--slow)
            INCLUDE_SLOW=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--file)
            FILE="$2"
            shift 2
            ;;
        -k|--keyword)
            KEYWORD="$2"
            shift 2
            ;;
        -m|--module)
            MODULE="$2"
            shift 2
            ;;
        -r|--report)
            REPORT=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查uv是否安装
check_uv() {
    print_info "检查uv..."

    if ! command -v uv &> /dev/null; then
        print_error "uv未安装，请先安装uv"
        print_info "安装方法: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    print_success "uv已就绪"
}

# 检查Python环境
check_python() {
    print_info "检查Python环境..."

    # 优先使用python3，其次使用python
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python未安装或不在PATH中"
        exit 1
    fi

    print_success "找到Python命令: $PYTHON_CMD"

    # 获取Python版本，处理可能的错误
    # 使用临时变量存储命令输出，避免set -e导致脚本退出
    PYTHON_VERSION_OUTPUT=$($PYTHON_CMD --version 2>&1) || true

    if [[ -n "$PYTHON_VERSION_OUTPUT" ]]; then
        # 尝试解析版本号
        PYTHON_VERSION=$(echo "$PYTHON_VERSION_OUTPUT" | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [[ -n "$PYTHON_VERSION" ]]; then
            print_info "Python版本: $PYTHON_VERSION (使用命令: $PYTHON_CMD)"

            if [[ "$PYTHON_VERSION" != "3.12" ]]; then
                print_warning "推荐使用Python 3.12，当前版本: $PYTHON_VERSION"
            fi
        else
            print_warning "无法解析Python版本，但将继续执行"
            print_info "Python版本输出: $PYTHON_VERSION_OUTPUT"
        fi
    else
        print_warning "无法获取Python版本，但将继续执行"
        print_info "使用命令: $PYTHON_CMD"
    fi
}

# 安装开发依赖
install_dev_dependencies() {
    print_info "安装开发依赖..."

    if uv sync --dev; then
        print_success "开发依赖安装完成"
    else
        print_error "开发依赖安装失败"
        exit 1
    fi
}

# 清理测试缓存
clean_cache() {
    print_info "清理测试缓存和报告..."

    # 删除pytest缓存
    rm -rf .pytest_cache
    rm -rf __pycache__
    rm -rf tests/__pycache__
    rm -rf tests/*/__pycache__

    # 删除覆盖率报告
    rm -rf htmlcov
    rm -f .coverage
    rm -f coverage.xml

    # 删除测试报告
    rm -f test-results.xml
    rm -f test-report.html

    print_success "清理完成"
}

# 构建pytest命令
build_pytest_command() {
    CMD="uv run pytest"

    # 添加详细输出
    if [[ "$VERBOSE" == true ]]; then
        CMD="$CMD -v"
    fi

    # 添加慢速测试
    if [[ "$INCLUDE_SLOW" == true ]]; then
        CMD="$CMD -m slow"
    fi

    # 添加覆盖率
    if [[ "$COVERAGE" == true ]]; then
        CMD="$CMD --cov=agnes --cov=web2 --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml"
    fi

    # 添加指定文件
    if [[ -n "$FILE" ]]; then
        CMD="$CMD $FILE"
    fi

    # 添加关键词过滤
    if [[ -n "$KEYWORD" ]]; then
        CMD="$CMD -k $KEYWORD"
    fi

    # 添加模块过滤
    if [[ -n "$MODULE" ]]; then
        case $MODULE in
            core)
                CMD="$CMD tests/core/"
                ;;
            skills)
                CMD="$CMD tests/skills/"
                ;;
            mcp)
                CMD="$CMD tests/mcp/"
                ;;
            web2)
                CMD="$CMD tests/web2/"
                ;;
            utils)
                CMD="$CMD tests/utils/"
                ;;
            integration)
                CMD="$CMD tests/integration/"
                ;;
            *)
                print_error "未知模块: $MODULE"
                print_info "可用模块: core, skills, mcp, web2, utils, integration"
                exit 1
                ;;
        esac
    fi

    # 添加单元测试标记
    if [[ "$RUN_UNIT" == true ]]; then
        CMD="$CMD -m 'not integration'"
    fi

    # 添加集成测试标记
    if [[ "$RUN_INTEGRATION" == true ]]; then
        CMD="$CMD -m integration"
    fi

    # 生成JUnit XML报告
    if [[ "$REPORT" == true ]]; then
        CMD="$CMD --junitxml=test-results.xml"
    fi

    echo "$CMD"
}

# 运行测试
run_tests() {
    print_info "开始运行测试..."
    print_info "========================================"

    # 构建命令
    CMD=$(build_pytest_command)
    print_info "执行命令: $CMD"

    # 运行测试
    if eval $CMD; then
        print_success "测试运行完成"
        return 0
    else
        print_error "测试运行失败"
        return 1
    fi
}

# 显示覆盖率报告
show_coverage_report() {
    if [[ "$COVERAGE" == true ]]; then
        print_info "覆盖率报告已生成:"
        print_info "  - 终端覆盖率报告: 见上方输出"
        print_info "  - HTML覆盖率报告: htmlcov/index.html"
        print_info "  - XML覆盖率报告: coverage.xml"

        # 根据操作系统打开HTML报告
        if [[ -f "htmlcov/index.html" ]]; then
            print_info "正在打开HTML覆盖率报告..."
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                # Windows
                start htmlcov/index.html
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                open htmlcov/index.html
            else
                # Linux
                xdg-open htmlcov/index.html
            fi
        fi
    fi
}

# 主函数
main() {
    print_info "AgnesAgent 测试运行脚本"
    print_info "========================================"

    # 清理缓存
    if [[ "$CLEAN" == true ]]; then
        clean_cache
        exit 0
    fi

    # 检查环境
    check_uv
    check_python

    # 安装开发依赖
    install_dev_dependencies

    # 运行测试
    if run_tests; then
        print_success "所有测试通过!"

        # 显示覆盖率报告
        show_coverage_report

        exit 0
    else
        print_error "测试失败!"
        exit 1
    fi
}

# 运行主函数
main
