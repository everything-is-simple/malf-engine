#!/bin/bash
# Day 0 验证脚本

echo "=========================================="
echo "第六刀 Day 0 验证脚本"
echo "=========================================="
echo ""

echo "1. 验证工具脚本..."
if [ -f "debug_t6.py" ]; then
    echo "   ✅ debug_t6.py 存在"
else
    echo "   ❌ debug_t6.py 不存在"
    exit 1
fi

echo ""
echo "2. 验证 P0 Fixtures..."
for fixture in R1_continuation_down_break_down_resolve R2_reversal_down_break_up_resolve R3_continuation_up_break_up_resolve R4_reversal_up_break_down_resolve; do
    if [ -f "tests/fixtures/range/${fixture}.json" ]; then
        echo "   ✅ ${fixture}.json 存在"
    else
        echo "   ❌ ${fixture}.json 不存在"
        exit 1
    fi
done

echo ""
echo "3. 验证文档..."
if [ -f "docs/T6-DAY-0-COMPLETION.md" ]; then
    echo "   ✅ T6-DAY-0-COMPLETION.md 存在"
else
    echo "   ❌ T6-DAY-0-COMPLETION.md 不存在"
    exit 1
fi

echo ""
echo "4. 运行工具验证..."
for fixture in r1 r2 r3 r4; do
    echo "   测试 ${fixture}..."
    /d/miniconda/py310/python.exe debug_t6.py ${fixture} > /tmp/verify_${fixture}.log 2>&1
    if [ $? -eq 0 ]; then
        final_state=$(grep "Final state:" /tmp/verify_${fixture}.log | tail -1)
        echo "   ✅ ${fixture}: ${final_state}"
    else
        echo "   ❌ ${fixture}: 执行失败"
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "✅ Day 0 验证通过！"
echo "=========================================="
echo ""
echo "交付物清单："
echo "  - debug_t6.py (22 KB)"
echo "  - 4 个 P0 fixture JSON 文件"
echo "  - T6-DAY-0-COMPLETION.md (16 KB)"
echo "  - TASK-SUMMARY.md (2.9 KB)"
echo ""
echo "下一步：执行 Day 1 任务（TDD 实现 Range 层）"
